from __future__ import annotations
import json
import pathlib
import sqlite3
import tempfile
import unittest
from unittest import mock

import v26_features as v26


class V26AdaptiveAITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=pathlib.Path(self.tmp.name)
        v26.BASE_DIR=root
        v26.DATA_DIR=root/'data'
        v26.CONTENT_DIR=root/'content'
        v26.CONTENT_DIR.mkdir(parents=True)
        v26.DB_PATH=root/'billinger.db'
        with sqlite3.connect(v26.DB_PATH) as c:
            c.execute('CREATE TABLE students(id INTEGER PRIMARY KEY, name TEXT)')
            c.execute("INSERT INTO students(id,name) VALUES(1,'Student')")
            c.execute('''CREATE TABLE online_questions(
                id TEXT PRIMARY KEY, tool TEXT, difficulty TEXT, prompt TEXT,
                ideal_answer TEXT, keywords TEXT, source_url TEXT,
                source_title TEXT, attribution TEXT, created_at TEXT)''')
        (v26.CONTENT_DIR/'question_bank.json').write_text(json.dumps({'questions':[
            {'id':f'q{i}','tool':'linux','difficulty':'Intermediate','prompt':f'Explain journalctl case {i}',
             'ideal_answer':'Use journalctl and systemctl with evidence and rollback.',
             'keywords':['journalctl','systemctl','evidence','rollback']} for i in range(1,8)
        ]}),encoding='utf-8')
        v26.init_v26_db()

    def tearDown(self):
        self.tmp.cleanup()

    def configure(self, provider: str, key: str='test-secret-key-123456789'):
        return v26.save_provider({'provider':provider,'enabled':True,'api_key':key,'daily_limit':100})

    def test_keys_are_encrypted_and_not_returned(self):
        public=self.configure('gemini','AIzaTestSecretValue1234567890')
        self.assertTrue(public['configured'])
        self.assertNotIn('AIzaTestSecretValue1234567890',json.dumps(public))
        with sqlite3.connect(v26.DB_PATH) as c:
            blob=c.execute("SELECT key_blob FROM ai_providers WHERE provider='gemini'").fetchone()[0]
        self.assertNotIn(b'AIzaTestSecretValue1234567890',bytes(blob))
        self.assertEqual(v26.unprotect_secret(blob),'AIzaTestSecretValue1234567890')

    def test_task_routes_are_editable_and_deduplicated(self):
        out=v26.save_task_route('test_analysis',['gemini','openai','gemini','invalid'])
        self.assertEqual(out['providers'],['gemini','openai'])
        self.assertEqual(v26.task_routes()['test_analysis'],['gemini','openai'])

    def test_quota_failure_falls_through_to_next_provider(self):
        self.configure('gemini'); self.configure('openai')
        v26.save_task_route('lesson_tutor',['gemini','openai'])
        calls=[]
        def fake(provider,model,key,task,messages,settings):
            calls.append(provider)
            if provider=='gemini':
                raise v26.ProviderFailure(provider,'quota exhausted',status=429,code='rate_limited',cooldown_seconds=60)
            return 'OpenAI fallback answer',{'input_tokens':5},200
        with mock.patch.object(v26,'_call_provider',side_effect=fake):
            result=v26.run_task('lesson_tutor',[{'role':'user','content':'Explain Docker'}],1)
        self.assertEqual(calls,['gemini','openai'])
        self.assertEqual(result['provider'],'openai')
        self.assertEqual(result['fallback_trace'][0]['status'],'rate_limited')

    def test_disabling_failover_stops_after_first_failure(self):
        self.configure('gemini'); self.configure('openai')
        v26.save_task_route('lesson_tutor',['gemini','openai'])
        v26.save_settings({'auto_failover':False})
        calls=[]
        def fake(provider,*args):
            calls.append(provider)
            raise v26.ProviderFailure(provider,'quota',status=429,code='rate_limited')
        with mock.patch.object(v26,'_call_provider',side_effect=fake):
            with self.assertRaisesRegex(ValueError,'gemini:rate_limited'):
                v26.run_task('lesson_tutor',[{'role':'user','content':'x'}],1)
        self.assertEqual(calls,['gemini'])

    def test_pii_and_secrets_are_redacted_before_provider_call(self):
        self.configure('groq')
        v26.save_task_route('lesson_tutor',['groq'])
        captured={}
        def fake(provider,model,key,task,messages,settings):
            captured['text']=messages[0]['content']
            return 'safe',{},200
        with mock.patch.object(v26,'_call_provider',side_effect=fake):
            v26.run_task('lesson_tutor',[{'role':'user','content':'Email me at person@example.com; key sk-12345678901234567890'}],1)
        self.assertIn('[REDACTED_EMAIL]',captured['text'])
        self.assertIn('[REDACTED_SECRET]',captured['text'])
        self.assertNotIn('person@example.com',captured['text'])

    def test_structured_test_analysis_is_saved(self):
        self.configure('openai')
        v26.save_task_route('test_analysis',['openai'])
        answer=json.dumps({'strong_areas':['Linux'],'weak_areas':['Kubernetes'],'missing_commands':['kubectl describe'],'revision_plan':['Repeat probe lab']})
        with mock.patch.object(v26,'_call_provider',return_value=(answer,{},200)):
            result=v26.analyze_test(1,{'session_id':'t1','tool':'kubernetes','score':62,'details':[]})
        self.assertEqual(result['analysis']['weak_areas'],['Kubernetes'])
        self.assertEqual(len(v26.recent_student_analyses(1)['analyses']),1)

    def test_question_generation_uses_local_verified_fallback(self):
        result=v26.generate_question_set(1,{'mode':'commands','tool':'linux','difficulty':'Intermediate','count':4})
        self.assertEqual(result['provider'],'local_fallback')
        self.assertEqual(len(result['questions']),4)
        answers=[{'id':q['id'],'answer':'journalctl systemctl evidence rollback'} for q in result['questions']]
        graded=v26.grade_question_set(1,result['session_id'],answers)
        self.assertGreaterEqual(graded['score'],75)

    def test_daily_provider_limit_skips_to_fallback(self):
        self.configure('gemini'); self.configure('openai')
        v26.save_provider({'provider':'gemini','enabled':True,'daily_limit':1})
        v26.save_task_route('lesson_tutor',['gemini','openai'])
        v26._log(1,'lesson_tutor','gemini','model','success',1,1,1,200)
        calls=[]
        def fake(provider,*args): calls.append(provider); return ('ok',{},200)
        with mock.patch.object(v26,'_call_provider',side_effect=fake):
            result=v26.run_task('lesson_tutor',[{'role':'user','content':'x'}],1)
        self.assertEqual(calls,['openai'])
        self.assertEqual(result['fallback_trace'][0]['status'],'local_daily_limit')

    def test_provider_key_table_excluded_from_json_backup(self):
        self.assertNotIn('ai_providers',v26.backup_tables())
        self.assertIn('ai_task_routes',v26.backup_tables())


    def test_provider_adapters_use_expected_official_shapes(self):
        settings=v26.get_settings(); messages=[{'role':'user','content':'hello'}]
        calls=[]
        def fake_http(url,payload,headers,timeout):
            calls.append((url,payload,headers))
            if 'generativelanguage' in url:
                return {'candidates':[{'content':{'parts':[{'text':'gemini ok'}]}}]},200
            if url.endswith('/responses'):
                return {'output_text':'openai ok'},200
            return {'choices':[{'message':{'content':'chat ok'}}]},200
        with mock.patch.object(v26,'_http_json',side_effect=fake_http):
            self.assertEqual(v26._call_provider('gemini','gemini-3.6-flash','key','lesson_tutor',messages,settings)[0],'gemini ok')
            self.assertEqual(v26._call_provider('openai','gpt-5.6-terra','key','test_analysis',messages,settings)[0],'openai ok')
            self.assertEqual(v26._call_provider('groq','openai/gpt-oss-20b','key','question_generation',messages,settings)[0],'chat ok')
            self.assertEqual(v26._call_provider('openrouter','openrouter/auto','key','company_interview',messages,settings)[0],'chat ok')
        self.assertIn(':generateContent',calls[0][0]); self.assertIn('x-goog-api-key',calls[0][2])
        self.assertEqual(calls[1][0],'https://api.openai.com/v1/responses'); self.assertIn('input',calls[1][1])
        self.assertEqual(calls[2][0],'https://api.groq.com/openai/v1/chat/completions')
        self.assertEqual(calls[3][0],'https://openrouter.ai/api/v1/chat/completions'); self.assertEqual(calls[3][1]['model'],'openrouter/auto')

    def test_provider_connection_test_uses_long_timeout_and_small_output(self):
        self.configure('openai')
        captured={}
        def fake(provider,model,key,task,messages,settings):
            captured.update(settings)
            return 'BILLINGER_OK',{},200
        with mock.patch.object(v26,'_call_provider',side_effect=fake):
            result=v26.test_provider('openai')
        self.assertTrue(result['ok'])
        self.assertGreaterEqual(captured['request_timeout_seconds'],120)
        self.assertEqual(captured['max_output_tokens'],128)
        self.assertTrue(captured['_connection_test'])


    def test_invalid_model_and_key_are_rejected(self):
        with self.assertRaises(ValueError): v26.save_provider({'provider':'openai','api_key':'short'})
        with self.assertRaises(ValueError): v26.save_provider({'provider':'openai','api_key':'long-enough-key-123','model':'bad model name'})


if __name__=='__main__':
    unittest.main()
