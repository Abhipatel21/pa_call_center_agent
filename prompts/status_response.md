You have the following information from the database regarding the prior authorization:

{{ lookup_result }}

Provide a **natural language summary** of the status. Do NOT output raw JSON or dictionaries.
Summarize the key details like Status, Validity Dates, and Notes.
If found, give details.
If not found, say so.

After providing the status, always ask: "Is there anything else I can assist you with?"

IMPORTANT:
If the `lookup_result` indicates "Auth ID not found", tell the user: "This authorization ID is not present." AND then asking them: "Could you please provide the procedure code or description instead?" (Do NOT ask "Is there anything else" in this specific case, as we are trying to recover).
If `lookup_result` is successful or generic "not found" (and no recovery possible), then ask "Is there anything else I can assist you with?"
