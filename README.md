# YaPOC

Yet another Proof of Concept

## Preamble

This project has been created to generate a Proof of concept for various approaches pre-receive git-hooks.

ATM there are three different approaches

1. python using git system calls
2. python using pygit2
3. go using git2go (to be implemented)

We started with python implementation because of good knowledge/skills across our team.
This makes it easier for us to review code and architecture and write our own code.
Go implementations can hopefully generated easily by AI.

## Current implementation details

* Reject files matching the following patterns
  * `.osc`
  * `*.obsinfo`
  * `*.obscpio`
* Allow exceptions for files list in `_allow_files_commit`


## How to start

With the following command 

```
make run_tests_in_kanku # (alias: rtik)
```

you can run all tests for all implementations.
A working kanku devel setup is required for this.
(additional container equivalent would be appreciated, but please don't break the kanku approach)

```
setup-env.sh
```

* Creates a bare repository
* Configures systemwide settings

```
test.py # (alternative: make test)
```

python implementation of integration tests

```
test.sh
```

deprecated first implementation of integration tests
