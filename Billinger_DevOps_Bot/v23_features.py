"""
Billinger v2.3 Features Layer: Company Simulation & Outage Scenario Engine
Directly integrates with labs.simulation and enterprise company scenarios.
"""
from labs.simulation import company_simulation, CompanySimulation

class VirtualCompanyEngine:
    """Simulates real-world enterprise infrastructure & business impact"""
    def __init__(self):
        self.simulation = company_simulation

    def get_active_scenarios(self):
        return self.simulation.list_scenarios()

    def get_scenario_by_id(self, scenario_id):
        return self.simulation.get_scenario(scenario_id)

    def evaluate_solution(self, scenario_id, commands):
        cmd_str = " ".join(commands) if isinstance(commands, list) else str(commands)
        return self.simulation.validate_solution(scenario_id, cmd_str)

company_engine = VirtualCompanyEngine()
