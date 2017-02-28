# Author: carstein <michal.melewski@gmail.com>
# Annotate function with prototype

import os
import sys
import json
from binaryninja import *

from stacks import linux_x86

stack_changing_llil = ['LLIL_STORE', 'LLIL_PUSH']
data_path = '/annotate/data/all_functions.json'

# Simple database loader - assume all is in one file for now
def load_database():
  fh = open(sys.path[0]+data_path, 'r')
  return json.load(fh)

# Function to be executed when we invoke plugin
def run_plugin(bv, function):
  # load database
  db = load_database()

  # logic of stack selection
  if bv.platform.name == 'linux-x86':
    stack = linux_x86.Stack()
  else:
    log_error('[x] Virtual stack not found for {platform}'.format(platform=bv.platform.name))
    return -1

  log_info('[*] Annotating function <{name}>'.format(name=function.symbol.name))

  for block in function.low_level_il:
    for instruction in block:
      if instruction.operation.name in stack_changing_llil:
        stack.update(instruction)
      if instruction.operation.name == 'LLIL_CALL':
        callee = bv.get_function_at(instruction.dest.value) # Fetching function in question

        if (callee.symbol.type.name == 'ImportedFunctionSymbol' and db.has_key(callee.name)):
          stack_args = iter(stack)

          for function_args in db[callee.name]:
            try:
              stack_instruction = stack_args.next()
              function.set_comment(stack_instruction.address, function_args)
            except StopIteration:
              log_error('[x] Virtual Stack Empty. Unable to find function arguments for <{}>'.format(callee.name))
