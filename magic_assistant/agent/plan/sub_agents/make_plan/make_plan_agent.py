from loguru import logger

from magic_assistant.agent.plan.sub_agents.make_plan.prompt import build_prompt, decode_llm_output
from magic_assistant.io.base_io import BaseIo

from magic_assistant.agent.plan.plan import Plan
from magic_assistant.message import Message
from magic_assistant.agent.base_agent import BaseAgent

class MakePlanAgent(BaseAgent):
    # _memory: SimpleMemory = None
    def init(self) -> int:
        # self._memory = SimpleMemory(agent_id=self.agent_id, orm_engine=self.orm_engine, memory_size=self.agent_config.memory_size)
        return 0

    async def run(self) -> Plan:
        person_input = await self.io.input()
        plan = self._init_plan(person_input=person_input)

        await self.output_intermediate_steps("%s:\n%s\n\n%s:\n%s\n" % (
            self.globals.tips.get_tips().PLAN.value, plan.original_plan_str,
            self.globals.tips.get_tips().EXPLANATION.value, plan.explanation))

        if self.agent_config.user_confirm_and_adjust:
            await self.io.output('Press "Enter" to continue. Or input your adjustment and press "Enter"\n')
            plan = await self._person_adjust(plan)

        logger.debug("_make_plan suc")
        return plan

    def _init_plan(self, person_input: str) -> Plan:
        message: Message = Message(self.agent_id)
        message.person_input = person_input
        prompt = build_prompt(message.person_input)
        message.llm_output = self.globals.llm_factory.run(prompt)
        plan: Plan = decode_llm_output(message.llm_output)
        plan.user_object = message.person_input
        if plan is None:
            logger.error("_make_plan failed, plan is None")
            return None

        # self._memory.add_message(message)
        return plan

    async def _person_adjust(self, plan: Plan) -> Plan:
        while True:
            message: Message = Message(self.agent_id)
            message.person_input = await self.io.input()
            if message.person_input.strip(" ").strip("\n").lower() == "":
                logger.debug("user confirmed")
                break
            else:
                logger.debug("user disagree, user input:%s" % message.person_input)

            # make_plan_prompt = MakePlanPrompt()
            prompt = build_prompt(plan.user_object, message.person_input)
            message.llm_output = self.globals.llm_factory.run(prompt)
            # self._memory.add_message(message)
            plan: Plan = decode_llm_output(message.llm_output)
            await self.io.output(self.globals.tips.get_tips().CONTINUE_OR_ADJUST.value)

        return plan
