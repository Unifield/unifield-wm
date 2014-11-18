#!/usr/bin/env bash

for i in `cat to_deactivate_for_finance_tests.list`; do mv $i deactivated/; done
