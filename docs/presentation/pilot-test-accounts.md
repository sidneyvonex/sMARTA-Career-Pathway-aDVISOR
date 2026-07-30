# Pilot presentation accounts

This is a safe account-reference template. It intentionally contains no password.

Prompt for one presentation-only password without putting it in shell history:

```powershell
$pilotDemoCredential = Get-Credential -UserName "pilot-demo" -Message "Enter the temporary demo password"
$env:PILOT_DEMO_PASSWORD = $pilotDemoCredential.GetNetworkCredential().Password
.\venv\Scripts\python.exe manage.py seed_pilot_demo
Remove-Item Env:PILOT_DEMO_PASSWORD
```

Do not commit the chosen password, paste it into screenshots, or reuse a personal password.
The command requires at least 10 characters and applies the supplied password to every
demo account. The `pilot-demo` username entered above is only a prompt label; use the
account emails below to sign in.

| Presentation role | Email | Demonstration state |
|---|---|---|
| System administrator | `system.admin@demo.smartashauri.test` | Five-county health, catalogue and audit events |
| School administrator | `school.admin@demo.smartashauri.test` | Kiambu school membership, counsellors and offerings |
| Counsellor 1 | `counsellor.one@demo.smartashauri.test` | Ready-for-review learner and completed-plan learner |
| Counsellor 2 | `counsellor.two@demo.smartashauri.test` | Learner who is beginning the journey |
| Learner — reviewed | `learner.ready@demo.smartashauri.test` | Evidence, assessment, choices and reviewed plan |
| Learner — needs review | `learner.review@demo.smartashauri.test` | Provisional choice and plan waiting for counsellor review |
| Learner — starting | `learner.starting@demo.smartashauri.test` | Academic evidence but no assessment or plan |
| Parent/guardian | `parent@demo.smartashauri.test` | Approved access to the reviewed learner |

## Local handling checklist

- [ ] Use a temporary presentation-only password.
- [ ] Keep the password in a local password manager or presenter note, not this file.
- [ ] Rerun the seed command before rehearsals; it is idempotent.
- [ ] Close private browser sessions after the presentation.
- [ ] Clear `PILOT_DEMO_PASSWORD` after use if it was set in the shell.
