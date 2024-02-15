#!/bin/bash

set -ex

dendro make-app-spec-file --app-dir dandi-vis-1 --spec-output-file dandi-vis-1/spec.json

dendro make-app-spec-file --app-dir neuroconv-1 --spec-output-file neuroconv-1/spec.json