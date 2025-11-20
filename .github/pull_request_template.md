# Pull Request Checklist

## Summary

- Provide a short, people-friendly description of the change.
- Call out risk areas, migrations, or rollout notes if applicable.

## Testing

- [ ] Not run (explain why)
- [ ] `make test` / targeted suites (`<command>`)
- [ ] Manual verification (describe)

## Documentation _(follow `DOCUMENTATION_UPDATE_PLAN.md`)_

- [ ] Not needed (pure refactor/tests)
- [ ] People-facing docs updated (quick start, guides, scenarios)
- [ ] Builder docs updated (platform overview, architecture, getting started)
- [ ] Service README/spec updated
- [ ] Entry added to `DOCUMENTATION_UPDATE_SUMMARY.md`
- [ ] Docs lint run locally if CI coverage was insufficient

> Tip: missing required documentation updates will block review.
