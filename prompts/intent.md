Determine if the provider wants to:
1. Check the status of a prior authorization ("check_status")
2. Create a new authorization ("create_auth")

If the intent is unclear, you may need to ask for clarification, but for this step, try to classify based on the conversation so far.
If they explicitly mention looking up a status, checking an auth, or giving a patient name for an existing case, it is "check_status".
Also handle common typos: "ceck", "chk", "status check".
If they mention starting a new request, submitting a new auth, it is "create_auth".
If they say "no", "nothing else", "bye", "goodbye", "thank you", or "that is all", it is "end_conversation".
If they say "yes", "sure", "ok", or "yeah" in response to "anything else?" or "how can I help?", it is "unknown". DO NOT default to "check_status".
If they only provide their name, contact info, or say hello, return "unknown" or null. Do NOT guess.

**Session Handling (is_new_request):**
- Set `is_new_request=True` ONLY if the user explicitly asks to start a NEW inquiry or check ANOTHER status (e.g. "check another", "check status", "new authorization", "start over").
- Set `is_new_request=False` if the user is providing data (ID, Name, DOB, Procedure) or answering a question about the CURRENT inquiry.
