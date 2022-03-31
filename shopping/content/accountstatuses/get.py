#!/usr/bin/python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Gets the status of the specified account."""

from __future__ import print_function
import argparse
import sys

from shopping.content import common

# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument(
    'account_id',
    nargs='?',
    default=0,
    type=int,
    help='The ID of the account for which to get information.')


def main(argv):
  # Authenticate and construct service.
  service, config, flags = common.init(
      argv, __doc__, parents=[argparser])
  merchant_id = config['merchantId']
  account_id = flags.account_id

  if not account_id:
    account_id = merchant_id
  elif merchant_id != account_id:
    common.check_mca(
        config,
        True,
        msg='Non-multi-client accounts can only get their own information.')

  status = service.accountstatuses().get(
      merchantId=merchant_id, accountId=merchant_id).execute()

  print('Account %s:' % status['accountId'])

  issue_count = 0
  if 'products' in status:
    for product in status['products']:
      issues = product['itemLevelIssues']
      for issue in issues:
        issue_count += 1
        print('  - Issue: [%s] "%s" affecting %s items' %
              (issue['code'],
               issue.setdefault('detail', ''),
               issue['numItems']))

  print('Total num of data quality issues: %d' % issue_count)


if __name__ == '__main__':
  main(sys.argv)
