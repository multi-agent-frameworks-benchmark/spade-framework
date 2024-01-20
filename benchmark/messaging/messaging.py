import spade
import sys
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import time
import csv
import datetime


DEFAULT_MAX_RECEIVE_LIMIT = "100:200:500:1000"
DEFAULT_HOST = "localhost"
AGENT_PASSWORD = "123456789"
SENDER_AGENT_JID = "sender_agent"
COUNTER_AGENT_JID = "counter_agent"

class Counter(Agent):

    def __init__(self, jid: str, password: str, receive_value_limit: int, sender_jid: str):
      super().__init__(jid, password)
      self.receive_value_limit = receive_value_limit
      self.sender_jid = sender_jid

    async def setup(self):
        
        self.counter_behaviour = self.CounterBehaviour(self.receive_value_limit, self.sender_jid)
        self.add_behaviour(self.counter_behaviour)

    class CounterBehaviour(CyclicBehaviour):

      def __init__(self, max_limit: int, send_to: str):
        super().__init__()
        self.max_limit = max_limit
        self.send_to = send_to

      async def run(self):
        msg = await self.receive(timeout=5)
        if msg is not None:
          await self.process_message(msg)
        else:
          await self.agent.stop()
      
      async def process_message(self,msg: Message):
        if msg.body == 'terminate':
          await self.handle_termination()
        else:
          await self.handle_increment_value(msg)
      
      async def handle_termination(self):
        print("Counter Agent {} received termination signal. Terminating...".format(str(self.agent.jid)))
        await self.agent.stop()
      
      async def handle_increment_value(self, msg: Message):
        received_value = int(msg.body) + 1

        print(f"Counter Agent {str(self.agent.jid)} received: {str(received_value)}")

        if received_value <= self.max_limit:
          await self.send_incremented_value(msg, received_value)
        else:
          await self.handle_value_limit_reached(msg)
      
      async def send_incremented_value(self, msg: Message, received_value: int):
        new_msg = Message(to=self.send_to)
        new_msg.set_metadata("performative", "inform")
        new_msg.body = str(received_value)
        await self.send(new_msg)

      async def handle_value_limit_reached(self, msg: Message):
        print(f"Counter Agent {str(self.agent.jid)} reached {str(self.max_limit)}. Notifying SenderAgent to terminate...")
        new_msg = Message(to=self.send_to)
        new_msg.set_metadata("performative", "inform")
        new_msg.body = "terminate"
        await self.send(new_msg)

        await self.agent.stop()

      
class Sender(Agent):
  def __init__(self, jid: str, password: str, receive_value_limit: int, counter_jid: str):
    super().__init__(jid, password)
    self.receive_value_limit = receive_value_limit
    self.counter_agent_jid = counter_jid
  
  async def setup(self):
        
    self.sender_behaviour = self.SenderBehaviour(self.receive_value_limit, self.counter_agent_jid)
    self.add_behaviour(self.sender_behaviour)

  class SenderBehaviour(CyclicBehaviour):

    def __init__(self, max_limit: int, send_to: str):
      super().__init__()
      self.max_limit = max_limit
      self.message_to = send_to
      self.current_value = 0

    async def run(self):
      await self.send_update_message()
      msg = await self.receive(timeout=5)
      await self.process_reply(msg)


    async def send_update_message(self):
      new_msg = Message(to=self.message_to)
      new_msg.set_metadata("performative", "inform")
      new_msg.body = str(self.current_value)
      await self.send(new_msg)

    async def process_reply(self, msg: Message):
      if msg is not None:
        await self.handle_received_message(msg)
      else:
        await self.agent.stop()
    
    async def handle_received_message(self, msg: Message):
      value = int(msg.body)
      self.current_value = value
      print(f"Sender Agent {str(self.agent.jid)} received {str(value)}")
      if value >= self.max_limit:
        await self.handle_value_limit_reached()

    async def handle_value_limit_reached(self):
      print(f"Sender Agent {str(self.agent.jid)} reached {str(self.max_limit)}. Notifying CounterAgent to terminate...")
      new_msg = Message(to=self.message_to)
      new_msg.set_metadata("performative", "inform")
      new_msg.body = "terminate"
      await self.send(new_msg)

      await self.agent.stop()

async def execute_benchmark_path(max_limit: int, host: str):
  agent_1_jid = f"{COUNTER_AGENT_JID}@{host}"
  agent_2_jid = f"{SENDER_AGENT_JID}@{host}"

  agent_1 = Counter(agent_1_jid, AGENT_PASSWORD, max_limit, agent_2_jid)
  agent_2 = Sender(agent_2_jid, AGENT_PASSWORD, max_limit,agent_1_jid)
  
  await agent_1.start()
  await agent_2.start()

  await spade.wait_until_finished([agent_1, agent_2])

async def main():

  args_length = len(sys.argv) - 1

  max_limit = sys.argv[1] if args_length > 0 else DEFAULT_MAX_RECEIVE_LIMIT
  max_limit = max_limit.split(":")
  host = sys.argv[2] if args_length > 1 else DEFAULT_HOST
  
  elapsed_times = []

  for i in max_limit:
    start = time.perf_counter()
    await execute_benchmark_path(int(i), host)
    elapsed = time.perf_counter() - start
    elapsed_times.append([int(i), elapsed])

  date_run = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  with open(f"{date_run}-benchmark-result-messaging.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Iteration", "Elapsed time"])
    for [iter, elapsed_time] in elapsed_times:
        writer.writerow([str(iter), str(elapsed_time)])
    
if __name__ == "__main__":
    spade.run(main())
    
