# 0013. A model is archived, never deleted

Date: 2026-08-20 Status: Accepted

## Context

A model is named by id from outside itself. An extractor points its specimen and serving roles at one (`docs/architecture.md`); every eval is history keyed by the job whose payload names the model it ran; `known_datasets` records what a model has trained on so an eval over seen data is visible as such. A user who has moved on from a model still wants it out of the way — the list of models an extractor offers is a working set, not an archive.

Deleting the row serves the second want and destroys the first. Eval history that names a model id becomes unreadable, and a role column pointing at the deleted row either falls to null without the user asking or blocks the delete with a foreign key error that names nothing a user recognises.

## Decision

A model carries `archived_at`. `POST /models/{id}/archive` sets it; nothing deletes a model.

An archived model is excluded from the models an extractor lists, and still reads through `GET /models/{id}`, so history that names it stays readable.

A model bound to either role cannot be archived, and an archived model cannot be set as a role. Clearing the role first is the user's decision to make, and making it explicit is what keeps a role from pointing at a model the user believes is gone.

## Consequences

Eval history stays readable for the lifetime of the extractor, and a role column always names a live model. Forking and training, which insert new models rather than editing one, no longer accumulate rows a user has to clean up by hand — archiving is the cleanup.

Every query that lists models filters on `archived_at`, and a query that forgets to shows a user rows they archived. The table grows without bound; reclaiming space means a retention decision this one does not make.

Reversing this means a hard delete plus a rule for what happens to the history and the role columns that name the row — which is the decision avoided here.
