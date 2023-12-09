import spade
from spade import agent
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

agent1_login = "test_agent@jabb.im"
agent1_password = "123456789"

agent2_login = "test_agent_2@jabb.im"
agent2_password = "123456789"

def create_message(receiver, metadata_key, metadata_value, body):

    msg = Message(to=receiver)
    msg.set_metadata(metadata_key, metadata_value)
    msg.body = body

    return msg

class SenderAgent(Agent):

    this_agent = agent1_login
    other_agent = agent2_login

    async def setup(self):
        
        self.sendingBehaviour = self.SendingBehaviour()
        self.add_behaviour(self.sendingBehaviour)

    class SendingBehaviour(CyclicBehaviour):

        async def run(self):
            
            msg = create_message(agent1_login, "performative", "inform", f"Hello agent {agent1_login}")
            await self.send(msg)
            print(f"{agent2_login}: Sent message to {agent1_login}")

class CounterAgent(Agent):

    async def setup(self):
        self.receivingBehaviour = self.ReceivingBehaviour()
        self.add_behaviour(self.receivingBehaviour)

    class ReceivingBehaviour(CyclicBehaviour):

        counter = 0

        async def run(self):
            msg = await self.receive(timeout=5)

            if (msg):

                self.counter += 1
                print(f"{agent1_login}: Got message from {agent2_login}. Number of counted messages: {self.counter}")

async def main():

    agent_1 = CounterAgent(agent1_login, agent1_password)
    agent_2 = SenderAgent(agent2_login, agent2_password)
    
    await agent_1.start()
    await agent_2.start()

if __name__ == "__main__":
    spade.run(main())