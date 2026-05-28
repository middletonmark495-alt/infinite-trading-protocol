import json
import uuid
from datetime import datetime
from typing import Dict, Any

# ── Tool Schema Definitions ───────────────────────────────────────────────────

ORCHESTRATOR_TOOLS = [
    {
        "name": "get_portfolio_status",
        "description": "Get full status of all businesses in the portfolio including stage, revenue, and pending tasks.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "create_new_business",
        "description": "Initialize a brand new online business from scratch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "niche": {"type": "string"},
                "model": {"type": "string", "enum": ["saas", "content", "ecommerce", "digital_product", "affiliate", "service"]},
                "description": {"type": "string"}
            },
            "required": ["name", "niche", "model", "description"]
        }
    },
    {
        "name": "dispatch_agent",
        "description": "Assign a task to a specialist agent and get their output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": ["researcher", "planner", "builder", "marketer", "finance", "growth"]},
                "task": {"type": "string"},
                "business_id": {"type": "string"},
                "context": {"type": "object"}
            },
            "required": ["agent", "task"]
        }
    },
    {
        "name": "update_business_status",
        "description": "Update the lifecycle status of a business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "status": {"type": "string", "enum": ["ideation", "planning", "building", "launching", "growing", "scaling", "paused"]},
                "notes": {"type": "string"}
            },
            "required": ["business_id", "status"]
        }
    },
    {
        "name": "set_next_actions",
        "description": "Set the prioritized list of next actions for a business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "agent": {"type": "string"},
                            "priority": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["business_id", "actions"]
        }
    }
]

RESEARCHER_TOOLS = [
    {
        "name": "generate_business_ideas",
        "description": "Generate profitable online business ideas in a given niche.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "count": {"type": "integer", "minimum": 1, "maximum": 10},
                "model_preference": {"type": "string", "enum": ["saas", "content", "ecommerce", "digital_product", "affiliate", "service", "any"]}
            },
            "required": ["category", "count"]
        }
    },
    {
        "name": "validate_idea",
        "description": "Validate whether a business idea has real market potential.",
        "input_schema": {
            "type": "object",
            "properties": {
                "idea": {"type": "string"},
                "target_market": {"type": "string"}
            },
            "required": ["idea", "target_market"]
        }
    },
    {
        "name": "analyze_competitor",
        "description": "Deep-dive analysis of a specific competitor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "competitor_name": {"type": "string"},
                "aspects": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["competitor_name"]
        }
    },
    {
        "name": "save_research_report",
        "description": "Save a research report to disk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title", "content"]
        }
    }
]

PLANNER_TOOLS = [
    {
        "name": "create_business_plan",
        "description": "Generate a comprehensive business plan document and save it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "name": {"type": "string"},
                "niche": {"type": "string"},
                "model": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["business_id", "name", "niche", "model", "description"]
        }
    },
    {
        "name": "create_mvp_spec",
        "description": "Define the minimum viable product specification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "business_type": {"type": "string"},
                "target_launch_days": {"type": "integer"}
            },
            "required": ["business_id", "business_type"]
        }
    },
    {
        "name": "create_financial_model",
        "description": "Build a 12-month financial projection model.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "model_type": {"type": "string"},
                "price_points": {"type": "array", "items": {"type": "number"}},
                "monthly_cost_estimate": {"type": "number"}
            },
            "required": ["business_id", "model_type"]
        }
    },
    {
        "name": "define_target_customer",
        "description": "Create a detailed ideal customer profile and persona.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "business_description": {"type": "string"}
            },
            "required": ["business_id", "business_description"]
        }
    }
]

BUILDER_TOOLS = [
    {
        "name": "save_landing_page",
        "description": "Save a complete HTML landing page file for a business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "html_content": {"type": "string", "description": "Complete HTML file content"}
            },
            "required": ["business_id", "html_content"]
        }
    },
    {
        "name": "save_product_file",
        "description": "Save a product code file to the business output directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "filename": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["business_id", "filename", "content"]
        }
    },
    {
        "name": "save_email_template",
        "description": "Save an HTML email template file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "template_name": {"type": "string"},
                "html_content": {"type": "string"}
            },
            "required": ["business_id", "template_name", "html_content"]
        }
    },
    {
        "name": "save_legal_doc",
        "description": "Save a legal document (ToS, Privacy Policy) as markdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "doc_type": {"type": "string", "enum": ["terms_of_service", "privacy_policy", "refund_policy"]},
                "content": {"type": "string"}
            },
            "required": ["business_id", "doc_type", "content"]
        }
    }
]

MARKETER_TOOLS = [
    {
        "name": "save_blog_post",
        "description": "Save a completed SEO blog post as markdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["business_id", "title", "content"]
        }
    },
    {
        "name": "save_email_sequence",
        "description": "Save a complete email drip sequence as a JSON file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "sequence_name": {"type": "string"},
                "emails": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "integer"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["business_id", "sequence_name", "emails"]
        }
    },
    {
        "name": "save_social_content",
        "description": "Save a batch of social media posts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "platform": {"type": "string"},
                "posts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["business_id", "platform", "posts"]
        }
    },
    {
        "name": "save_seo_strategy",
        "description": "Save an SEO strategy and content calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["business_id", "content"]
        }
    }
]

FINANCE_TOOLS = [
    {
        "name": "log_revenue",
        "description": "Log a revenue event for a business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "amount": {"type": "number"},
                "source": {"type": "string"}
            },
            "required": ["business_id", "amount", "source"]
        }
    },
    {
        "name": "log_expense",
        "description": "Log an expense for a business.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "amount": {"type": "number"},
                "category": {"type": "string"}
            },
            "required": ["business_id", "amount", "category"]
        }
    },
    {
        "name": "generate_pnl_report",
        "description": "Generate and save a profit and loss report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "period": {"type": "string", "enum": ["weekly", "monthly", "quarterly", "all-time"]}
            },
            "required": ["business_id"]
        }
    },
    {
        "name": "calculate_unit_economics",
        "description": "Calculate LTV, CAC, payback period, and margin.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "avg_revenue_per_user": {"type": "number"},
                "churn_rate": {"type": "number"},
                "cac": {"type": "number"}
            },
            "required": ["business_id", "avg_revenue_per_user", "churn_rate"]
        }
    }
]

GROWTH_TOOLS = [
    {
        "name": "save_growth_experiment",
        "description": "Design and save a growth experiment or A/B test.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "hypothesis": {"type": "string"},
                "metric_to_improve": {"type": "string"},
                "experiment_type": {"type": "string"},
                "details": {"type": "string"}
            },
            "required": ["business_id", "hypothesis", "metric_to_improve", "experiment_type", "details"]
        }
    },
    {
        "name": "save_referral_program",
        "description": "Save a designed referral or affiliate program.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["business_id", "content"]
        }
    },
    {
        "name": "save_scaling_playbook",
        "description": "Save a step-by-step scaling playbook.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_id": {"type": "string"},
                "current_mrr": {"type": "number"},
                "target_mrr": {"type": "number"},
                "content": {"type": "string"}
            },
            "required": ["business_id", "content"]
        }
    }
]


# ── Tool Implementations ──────────────────────────────────────────────────────

class ToolRegistry:
    """Implements all tool handlers for all agents."""

    def __init__(self, state_manager, message_bus, agent_registry=None):
        self.state = state_manager
        self.bus = message_bus
        self.agent_registry = agent_registry or {}

    def execute(self, agent_name: str, tool_name: str, tool_input: Dict) -> str:
        handler = getattr(self, f"_tool_{tool_name}", None)
        if not handler:
            return f"Error: unknown tool '{tool_name}'"
        try:
            result = handler(agent_name, tool_input)
            return json.dumps(result) if isinstance(result, (dict, list)) else str(result)
        except Exception as e:
            return f"Tool error: {e}"

    # ── Orchestrator ──────────────────────────────────────────────────────────

    def _tool_get_portfolio_status(self, agent: str, inp: Dict) -> Dict:
        businesses = self.state.list_businesses()
        return {
            "total_businesses": len(businesses),
            "businesses": [
                {
                    "id": b["id"], "name": b["name"], "niche": b.get("niche"),
                    "model": b.get("model"), "status": b.get("status"),
                    "revenue": b.get("revenue", 0), "expenses": b.get("expenses", 0),
                    "next_actions": b.get("next_actions", [])
                }
                for b in businesses
            ],
            "recent_activity": self.state.get_agent_log(limit=5)
        }

    def _tool_create_new_business(self, agent: str, inp: Dict) -> Dict:
        business = self.state.create_business(
            name=inp["name"], niche=inp["niche"],
            model=inp["model"], description=inp["description"]
        )
        self.bus.broadcast(agent, f"New business created: {inp['name']}", {"business_id": business["id"]})
        return {"success": True, "business_id": business["id"],
                "message": f"Business '{inp['name']}' created with ID {business['id']}"}

    def _tool_dispatch_agent(self, agent: str, inp: Dict) -> str:
        target = inp["agent"]
        if target in self.agent_registry:
            return self.agent_registry[target].run(
                inp["task"],
                context=inp.get("context", {}),
                business_id=inp.get("business_id")
            )
        return f"Agent '{target}' not registered. Available: {list(self.agent_registry.keys())}"

    def _tool_update_business_status(self, agent: str, inp: Dict) -> Dict:
        self.state.update_business(inp["business_id"], {
            "status": inp["status"],
            "status_notes": inp.get("notes", "")
        })
        return {"success": True, "business_id": inp["business_id"], "new_status": inp["status"]}

    def _tool_set_next_actions(self, agent: str, inp: Dict) -> Dict:
        self.state.update_business(inp["business_id"], {"next_actions": inp["actions"]})
        return {"success": True, "actions_set": len(inp["actions"])}

    # ── Researcher ────────────────────────────────────────────────────────────

    def _tool_generate_business_ideas(self, agent: str, inp: Dict) -> Dict:
        return {"category": inp["category"], "count": inp["count"],
                "model_preference": inp.get("model_preference", "any"),
                "status": "generating — include your ideas in the response text"}

    def _tool_validate_idea(self, agent: str, inp: Dict) -> Dict:
        return {"idea": inp["idea"], "target_market": inp["target_market"],
                "status": "validating — include your analysis in the response text"}

    def _tool_analyze_competitor(self, agent: str, inp: Dict) -> Dict:
        return {"competitor": inp["competitor_name"],
                "aspects": inp.get("aspects", ["pricing", "features", "positioning"]),
                "status": "analyzing — include your analysis in the response text"}

    def _tool_save_research_report(self, agent: str, inp: Dict) -> Dict:
        business_id = inp.get("business_id", "general")
        slug = inp["title"].lower().replace(" ", "_")[:50]
        path = self.state.save_output(business_id, "research", f"{slug}.md", inp["content"])
        return {"success": True, "saved_to": path}

    # ── Planner ───────────────────────────────────────────────────────────────

    def _tool_create_business_plan(self, agent: str, inp: Dict) -> Dict:
        bid = inp["business_id"]
        self.state.update_business(bid, {"business_plan": {"created_at": datetime.utcnow().isoformat()}})
        return {"status": "generating — write the full plan in your response text, then I will save it",
                "business_id": bid}

    def _tool_create_mvp_spec(self, agent: str, inp: Dict) -> Dict:
        self.state.update_business(inp["business_id"],
            {"mvp_spec": {"target_launch_days": inp.get("target_launch_days", 30)}})
        return {"status": "generating — write the full spec in your response", "business_id": inp["business_id"]}

    def _tool_create_financial_model(self, agent: str, inp: Dict) -> Dict:
        return {"status": "generating — write the financial model in your response",
                "business_id": inp["business_id"]}

    def _tool_define_target_customer(self, agent: str, inp: Dict) -> Dict:
        return {"status": "generating — write the ICP in your response", "business_id": inp["business_id"]}

    # ── Builder ───────────────────────────────────────────────────────────────

    def _tool_save_landing_page(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "website", "index.html", inp["html_content"])
        self.state.update_business(inp["business_id"], {"website": path})
        return {"success": True, "saved_to": path}

    def _tool_save_product_file(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "product", inp["filename"], inp["content"])
        return {"success": True, "saved_to": path}

    def _tool_save_email_template(self, agent: str, inp: Dict) -> Dict:
        fname = f"{inp['template_name'].lower().replace(' ', '_')}.html"
        path = self.state.save_output(inp["business_id"], "emails", fname, inp["html_content"])
        return {"success": True, "saved_to": path}

    def _tool_save_legal_doc(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "legal", f"{inp['doc_type']}.md", inp["content"])
        return {"success": True, "saved_to": path}

    # ── Marketer ──────────────────────────────────────────────────────────────

    def _tool_save_blog_post(self, agent: str, inp: Dict) -> Dict:
        slug = inp["title"].lower().replace(" ", "-")[:60]
        path = self.state.save_output(inp["business_id"], "content", f"{slug}.md", inp["content"])
        data = self.state.get_business(inp["business_id"])
        if data:
            pieces = data.get("content_pieces", [])
            pieces.append({"type": "blog_post", "title": inp["title"], "path": path})
            self.state.update_business(inp["business_id"], {"content_pieces": pieces})
        return {"success": True, "saved_to": path}

    def _tool_save_email_sequence(self, agent: str, inp: Dict) -> Dict:
        fname = f"{inp['sequence_name'].lower().replace(' ', '_')}_sequence.json"
        path = self.state.save_output(
            inp["business_id"], "emails", fname,
            json.dumps(inp["emails"], indent=2)
        )
        return {"success": True, "saved_to": path, "email_count": len(inp["emails"])}

    def _tool_save_social_content(self, agent: str, inp: Dict) -> Dict:
        fname = f"{inp['platform']}_posts.json"
        path = self.state.save_output(
            inp["business_id"], "social", fname,
            json.dumps(inp["posts"], indent=2)
        )
        return {"success": True, "saved_to": path, "post_count": len(inp["posts"])}

    def _tool_save_seo_strategy(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "marketing", "seo_strategy.md", inp["content"])
        return {"success": True, "saved_to": path}

    # ── Finance ───────────────────────────────────────────────────────────────

    def _tool_log_revenue(self, agent: str, inp: Dict) -> Dict:
        data = self.state.get_business(inp["business_id"])
        if data:
            revenue = data.get("revenue", 0) + inp["amount"]
            self.state.update_business(inp["business_id"], {"revenue": revenue})
            self.state.log_metric(inp["business_id"], "revenue", revenue)
        return {"success": True, "amount": inp["amount"], "source": inp["source"]}

    def _tool_log_expense(self, agent: str, inp: Dict) -> Dict:
        data = self.state.get_business(inp["business_id"])
        if data:
            expenses = data.get("expenses", 0) + inp["amount"]
            self.state.update_business(inp["business_id"], {"expenses": expenses})
        return {"success": True, "amount": inp["amount"], "category": inp["category"]}

    def _tool_generate_pnl_report(self, agent: str, inp: Dict) -> Dict:
        data = self.state.get_business(inp["business_id"])
        if not data:
            return {"error": "Business not found"}
        revenue = data.get("revenue", 0)
        expenses = data.get("expenses", 0)
        profit = revenue - expenses
        report = {
            "business": data["name"], "period": inp.get("period", "all-time"),
            "revenue": revenue, "expenses": expenses, "profit": profit,
            "margin": f"{(profit/revenue*100):.1f}%" if revenue > 0 else "N/A"
        }
        content = json.dumps(report, indent=2)
        self.state.save_output(inp["business_id"], "finance", "pnl_report.json", content)
        return report

    def _tool_calculate_unit_economics(self, agent: str, inp: Dict) -> Dict:
        arpu = inp["avg_revenue_per_user"]
        churn = inp["churn_rate"]
        cac = inp.get("cac", 0)
        ltv = arpu / churn if churn > 0 else 0
        payback = cac / arpu if arpu > 0 else 0
        result = {
            "ltv": round(ltv, 2), "cac": cac,
            "ltv_cac_ratio": round(ltv / cac, 2) if cac > 0 else "N/A",
            "payback_months": round(payback, 1),
            "monthly_churn": f"{churn*100:.1f}%"
        }
        self.state.save_output(
            inp["business_id"], "finance", "unit_economics.json",
            json.dumps(result, indent=2)
        )
        return result

    # ── Growth ────────────────────────────────────────────────────────────────

    def _tool_save_growth_experiment(self, agent: str, inp: Dict) -> Dict:
        experiment = {
            "id": str(uuid.uuid4())[:8],
            "hypothesis": inp["hypothesis"],
            "metric": inp["metric_to_improve"],
            "type": inp["experiment_type"],
            "details": inp["details"],
            "status": "designed",
            "created_at": datetime.utcnow().isoformat()
        }
        data = self.state.get_business(inp["business_id"])
        if data:
            experiments = data.get("growth_experiments", [])
            experiments.append(experiment)
            self.state.update_business(inp["business_id"], {"growth_experiments": experiments})
        self.state.save_output(
            inp["business_id"], "growth",
            f"experiment_{experiment['id']}.json",
            json.dumps(experiment, indent=2)
        )
        return {"success": True, "experiment_id": experiment["id"]}

    def _tool_save_referral_program(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "growth", "referral_program.md", inp["content"])
        return {"success": True, "saved_to": path}

    def _tool_save_scaling_playbook(self, agent: str, inp: Dict) -> Dict:
        path = self.state.save_output(inp["business_id"], "growth", "scaling_playbook.md", inp["content"])
        return {"success": True, "saved_to": path}
