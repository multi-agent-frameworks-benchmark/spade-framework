import spade
import sys
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
import time
import csv
import datetime

#Podajesz liczbe agentow dla danej iteracji
DEFAULT_PARAMS = "5:10:20:30"
DEFAULT_HOST = "localhost"
AGENT_PASSWORD = "123456789"
AGENT_BASE_JID = "helloWorldAgent"

class HelloWorldAgent(Agent):

  async def setup(self):
     self.add_behaviour(self.AgentBehavoiur())
    
  class AgentBehavoiur(OneShotBehaviour):
    async def run(self):
      print("Hello World! I'm agent {}".format(str(self.agent.jid)))        
      await self.agent.stop()


async def execute_benchmark_path(number_of_agents: int, host: str):
  agent_list = []

  for i in range(number_of_agents):
    agent = HelloWorldAgent(f'{AGENT_BASE_JID}-{i}@{host}', AGENT_PASSWORD)
    agent_list.append(agent)
    await agent.start()

  await spade.wait_until_finished(agent_list)

async def main():

  args_length = len(sys.argv) - 1
  params = sys.argv[1] if args_length > 0 else DEFAULT_PARAMS
  params = params.split(':')
  host = sys.argv[2] if args_length > 1 else DEFAULT_HOST

  elapsed_times = []

  for i in params:
    start = time.perf_counter()
    await execute_benchmark_path(int(i), host)
    elapsed = time.perf_counter() - start
    elapsed_times.append([int(i), elapsed])

  date_run = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  with open(f"{date_run}-benchmark-result-hello.csv", "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(["Iteration", "Elapsed time"])
      for [iter, elapsed_time] in elapsed_times:
         writer.writerow([str(iter), str(elapsed_time)])

if __name__ == "__main__":
  spade.run(main())
    