from spade import agent
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

agent1_login = ""
agent1_password = ""

agent2_login = ""
agent2_password = ""

def create_message(receiver, metadata_key, metadata_value, body):

    msg = Message(to=receiver)
    msg.set_metadata(metadata_key, metadata_value)
    msg.body = body

    return msg

class FirstCounterAgent(Agent):

    this_agent = agent1_login
    other_agent = agent2_login

    async def setup(self):
        pass

class SecondCounterAgent(Agent):

    this_agent = agent2_login
    other_agent = agent1_login

    async def setup(self):
        pass

    class ReceivingBehaviour(CyclicBehaviour):

        async def run(self):
            msg = await self.receive(timeout=5)

            if (msg):

                number = msg.body
                number += 1

                msg = create_message(self.other_agent, "performative", "inform", str(number))

                await self.send(msg)
                print(f"{self.this_agent}: Got {msg.body}, resent {number}")


if __name__ == "__main__":

    pass