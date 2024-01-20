import spade
import sys
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from spade.message import Message
import random 
import time
import csv
import datetime
import os

DEFAULT_NUMBER_OF_CONTRACTORS = "2:4:8"
DEFAULT_IF_ELAPSED_WITH_CREATION_AGENT = "True"
DEFAULT_HOST = "localhost"
AGENT_PASSWORD = "123456789"
INITIATOR_AGENT_JID = "initiator_agent"
CONTRACTOR_AGENT_BASE_JID = "contractor_agent"

PROPOSE = "propose"
REJECT = "reject-proposal"
NO_ANSWER = "no_answer"

class InitiatorAgent(Agent):

  def __init__(self, jid: str, password: str, contractor_jids: list[str]):
    super().__init__(jid, password)
    self.contractor_jids = [[x, None] for x in contractor_jids]
    self.current_contractor_index = 0
    
  async def setup(self):
    print("Initiator Agent {} is ready.".format(str(self.jid)))
    self.initiator_behaviour = self.InitiatorBehaviour()
    self.add_behaviour(self.initiator_behaviour)
   
  class InitiatorBehaviour(CyclicBehaviour):

    async def on_end(self):
      await self.agent.stop()
    
    async def run(self):

      if self.agent.current_contractor_index >= len(self.agent.contractor_jids):
        self.kill()
        return

      current_contractor = self.agent.contractor_jids[self.agent.current_contractor_index]
      await self.send_call_for_proposal(current_contractor)
      await self.handling_response_from_contractor(current_contractor)

    async def send_call_for_proposal(self,current_contractor: list[str, str]):
      new_msg = Message(to=current_contractor[0])
      new_msg.set_metadata("performative", "cfp")
      new_msg.body = "Details: Design and implement a new e-commerce website with payment gateway integration."

      await self.send(new_msg)
    
    async def handling_response_from_contractor(self, current_contractor: list[str, str]):
      msg = await self.receive(timeout=5)
      if msg is not None:
        self.process_message(msg, current_contractor)
      else:
        current_contractor[1] = NO_ANSWER

      self.agent.current_contractor_index += 1
        
    def process_message(self, msg: Message, current_contractor: list[str, str]):
      if msg.get_metadata("performative") == "propose":
        print(f"Initiator Agent {str(self.agent.jid)} received proposal from {current_contractor[0]}")
        current_contractor[1] = PROPOSE
      elif msg.get_metadata("performative") == "reject-proposal":
        current_contractor[1] = REJECT

class ContractorAgent(Agent):

  def __init__(self, jid: str, password: str, initiator_jid: str):
    super().__init__(jid, password)
    self.initiator_jid = initiator_jid 
    
  async def setup(self):
    print("Contractor Agent {} is ready.".format(str(self.jid)))
    self.contractor_behaviour = self.ContractorBehaviour()
    self.add_behaviour(self.contractor_behaviour)

  class ContractorBehaviour(CyclicBehaviour):

    async def on_end(self):
      await self.agent.stop()
    
    async def run(self):
      msg = await self.receive(timeout=10)
      if msg is not None:
        await self.process_message(msg)
      else:
        self.kill()

    async def process_message(self, msg: Message):
      if msg.get_metadata("performative") == "cfp":
        decision = "propose" if random.random() > 0.5 else "reject-proposal"
        new_msg = Message(to=self.agent.initiator_jid)
        new_msg.set_metadata("performative", decision)
        await self.send(new_msg)
      
      self.kill()


async def execute_benchmark_path(number_of_contractors: int, with_creation_of_agent: bool, host: str):
  contractor_agent_list = []
  contractor_agent_jid_list = []

  start = None

  if with_creation_of_agent:
    start = time.perf_counter()

  for i in range(number_of_contractors):
    agent = ContractorAgent(f"{CONTRACTOR_AGENT_BASE_JID}-{i}@{host}", AGENT_PASSWORD, f"{INITIATOR_AGENT_JID}@{host}")
    contractor_agent_list.append(agent)
    contractor_agent_jid_list.append(f"{CONTRACTOR_AGENT_BASE_JID}-{i}@{host}")
  
  initiator_agent = InitiatorAgent( f"{INITIATOR_AGENT_JID}@{host}", AGENT_PASSWORD, contractor_agent_jid_list)
  
  if with_creation_of_agent == False:
    start = time.perf_counter()

  for a in contractor_agent_list:
    await a.start()

  await initiator_agent.start()

  agent_list = contractor_agent_list
  agent_list.append(initiator_agent)

  await spade.wait_until_finished(agent_list)

  elapsed = time.perf_counter() - start

  return elapsed

async def main():

  args_length = len(sys.argv) - 1

  number_of_contractors = sys.argv[1] if args_length > 0 else DEFAULT_NUMBER_OF_CONTRACTORS
  number_of_contractors = number_of_contractors.split(":")
  if_elapsed_with_agent_creations = sys.argv[2] if args_length > 1 else DEFAULT_IF_ELAPSED_WITH_CREATION_AGENT
  if_elapsed_with_agent_creations = True if if_elapsed_with_agent_creations == 'True' else False
  # host = sys.argv[2] if args_length > 2 else DEFAULT_HOST
  host = "server_cnp"

  elapsed_times = []

  for i in number_of_contractors:
    elapsed = await execute_benchmark_path(int(i), if_elapsed_with_agent_creations, host)
    elapsed_times.append([int(i), elapsed])
  
  current_directory = os.getcwd()

  target_directory = os.path.abspath(os.path.join(current_directory, '..', '..'))

  benchmark_results_directory = os.path.join(target_directory, 'benchmark-results')
  os.makedirs(benchmark_results_directory, exist_ok=True)

  date_run = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  file_path = os.path.join(benchmark_results_directory, f"{date_run}-benchmark-result-contract-net-protocol.csv")

  # Open the file in the specified directory
  with open(file_path, "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(["Iteration", "Elapsed time"])
      for [iter, elapsed_time] in elapsed_times:
          writer.writerow([str(iter), str(elapsed_time)])


if __name__ == "__main__":
  spade.run(main())
    