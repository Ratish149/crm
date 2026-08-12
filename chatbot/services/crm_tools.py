CRM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_conversion_pipeline",
            "description": "Get lead funnel counts per stage and conversion rates between stages (new -> discovery -> quoted -> negotiation -> closed), optionally within a date range",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "ISO date, optional"},
                    "end_date": {"type": "string", "description": "ISO date, optional"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lead_stats",
            "description": "Get counts of leads grouped by status and source, optionally within a date range",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "ISO date, optional"},
                    "end_date": {"type": "string", "description": "ISO date, optional"},
                    "status": {
                        "type": "string",
                        "enum": ["new", "not_interested", "discovery", "quoted", "negotiation", "closed", "all"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_leads",
            "description": "Search leads by name, email, or status",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "matches full_name or email"},
                    "status": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lead_detail",
            "description": "Get full profile for a single lead including recent activity, by lead id or exact full name",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "full_name": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_followups",
            "description": "Get pending follow-up tasks, optionally for a specific lead or only ones created by the requesting user",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "only_mine": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search internal knowledge base articles by keyword",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_leads",
            "description": "Get the most recently created leads, optionally filtered by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer", 
                        "description": "max leads to return(default 5)",
                    },
                    "status": {
                        "type": "string"
                    },
                },
            },
        },
    },
]