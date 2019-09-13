#!/bin/bash

pg_restore -U postgres --dbname=acts_ph4 -n ntg --verbose --single-transaction < backup/acts_ph4.dump
