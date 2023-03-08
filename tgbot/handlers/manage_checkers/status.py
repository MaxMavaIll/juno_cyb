import logging
from datetime import datetime
from socket import EAI_SERVICE
import asyncio
import json

from name_node import name
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from api.config import nodes
from api.functions import get_index_by_moniker
from api.requests import MintScanner
from schedulers.jobs import add_user_checker
from tgbot.handlers.manage_checkers.router import checker_router
from tgbot.misc.states import Status
from tgbot.keyboards.inline import validator_moniker
from tgbot.keyboards.inline import menu, list_validators, to_menu

import os
from api.config import nodes
from api.functions import load_block





# @checker_router.callback_query(text="status")
# async def create_checker(callback: CallbackQuery, state: FSMContext):
#     """Entry point for create checker conversation"""

#     # data = await state.get_data()
#     # validators = data.get('validators')

#     # if validators:
#     #     all_valid = [validator["operator_address"] 
#     #                  for num, validator in validators.items()]
#     #     logging.info(f"{all_valid}")
#         # await message.answer("Вибири валідатора:", reply_markup=validator_moniker(all_valid).as_markup())
#     await callback.message.edit_text(
#     'Let\'s see...\n'
#     "The status of which validator do you want to know?"
#     )
    
    
@checker_router.callback_query(text="status")
async def create_checker(callback: CallbackQuery, state: FSMContext):
    """Entry point for create checker conversation"""

    data = await state.get_data()
    name_node = name

    validators = data.get('validators', {})
    validators = [f'{validator["operator_address"]}'
            for num, validator in enumerate(validators.values(), 1)]

    if validators:
        await callback.message.edit_text(
            'Let\'s see...\n'
            "The status of which validator do you want to know?",
            reply_markup=list_validators(validators, "status")
        )
    
    else:
        await callback.answer(
            'Sorry, but I didn\'t find any checker. \n'
            'First, create a checker',
            # show_alert=True
        )
    
    

    


#
# @checker_router.message(state=CreateChecker.chain)
# async def enter_chain(message: Message, state: FSMContext):
#     """Enter chain name"""
#     data = await state.get_data()
#     if message.text in nodes.keys():
#         data['chain'] = message.text
#
#         await message.answer(
#             'Okay, now I need the name of this validator'
#         )
#         await state.set_state(CreateChecker.operator_address)
#         await state.update_data(data)
#     else:
#         await message.answer(
#             'Sorry, but we dont have this validator\'s network\n'
#             'Try again'
#         )


@checker_router.callback_query(Text(text_startswith="status&"))
async def enter_operator_address(callback: CallbackQuery, state: FSMContext,
                                 scheduler: AsyncIOScheduler,
                                 mint_scanner: MintScanner):
    """Enter validator's name"""
    moniker = callback.data.split("&")[-1]
    data = await state.get_data()
    name_node = name
    validators_data = data.get("validators")


    # validators = await mint_scanner.get_validator(name_node)
    validators = await mint_scanner.get_validators(name_node) # list validators
    validator = get_index_by_moniker(moniker, validators) # index validators
    data_new = await mint_scanner.parse_application(name, moniker)
    logging.info(data_new['missed_blocks_counter'])
    missed_blocks_counter = int(data_new['missed_blocks_counter'])
    logging.info(f'Got {validator} {validators[validator]} validators')
    validators = validators[validator]

    if validators["jailed"]:
        validators["jailed"] = '🔴 true'
    else:
        validators["jailed"] = '🟢 false'

    if validators["status"] == "BOND_STATUS_BONDED":
        status = "🟢 BONDED"
    else:
        status = "🔴 UNBONDED"

    await callback.answer(
        f'status: '
        f'\n    moniker: {validators["description"]["moniker"]}'
        f'\n    VOTING POWER: {validators["tokens"]}'
        f'\n    Jailed:  {validators["jailed"]}'
        f'\n    validators status: {status}'
        f'\n    missed blocks: {missed_blocks_counter}',
        show_alert=True, 
    )
