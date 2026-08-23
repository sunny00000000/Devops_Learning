# Administrator Guide — Billinger Bot v2.9.0

## 1. Configure administrator access

Open **Admin Control** and choose **Configure or unlock**. Set a PIN with 4–30 characters, then enter the administrator and institute names. The PIN hash is stored only in the local SQLite database.

Keep the PIN safely. There is no cloud recovery. For a fresh installation without records, local data can be reset with `Reset_Local_Data.bat`; this removes student progress as well as the administrator configuration.

## 2. Configure students

Use the student selector and administrator performance table to review profiles. For each learner, set the target role, daily study minutes, interview date, and active track. The current release supports up to 10 local profiles.

## 3. Create batches

In **Students & batches**, create a name, description, target role, level, and deadline. Add or remove students using the membership controls. A student may belong to more than one batch.

## 4. Assign work

In **Assignments**, choose a batch and assign a lesson, practice lab, test, practical exam, project, interview, or custom activity. Include a due date and exact evidence requirements. Post announcements separately for schedule or classroom messages.

## 5. Import learning documents safely

Upload a ZIP through **Verified importer**. Review every grouped resource. Do not publish until the primary tool is correct. Use Program Library for institute-wide handbooks that should not appear inside a technical tool.

The importer recommendation is assistance, not final authority. Check the title, table of contents, dominant subject, level, duplicates, and current version before publishing.

## 6. Review practical evidence

Automatic practical scores are a first-level rubric. Review the student’s project workspace, commands, screenshots, configuration files, validation output, security decisions, and rollback plan before approving high-stakes completion.

## 7. Issue certificates

Open **Certificates & Reports**, select the student, type, subject, and verified score. Generate the certificate only after the evidence is approved. Store or print the downloaded HTML certificate. Its verification code can be checked inside the same local bot installation.

## 8. Back up the institute

Create a full backup before importing content, applying an update, restoring data, or moving the hard disk. Download or copy the resulting ZIP from `backups\` to a separate disk. A backup stored only on the same hard disk does not protect against disk failure.

## 9. Restore or update

Stage the ZIP from the administrator maintenance page. Then:

1. Close the Billinger command window.
2. Run `Apply_Pending_Restore.bat` or `Apply_Pending_Update.bat`.
3. Review the console result.
4. Start the bot and run `Run_Self_Test.bat` when required.

The maintenance tool creates a safety copy and refuses packages that fail structural validation.
