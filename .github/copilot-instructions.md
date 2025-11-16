## 1. General Principles
	•	Write clean, modern, production-ready code.
	•	Prefer clarity over cleverness.
	•	Keep everything modular and scalable.
	•	Remove duplication whenever possible.
	•	Use modern syntax and best practices.

⸻

## 2. Templates (Jinja2)
	•	Use Jinja2 in all HTML templates.
	•	Structure pages with:
	•	{% extends "base.html" %}
	•	{% block content %}{% endblock %}
	•	{% include "components/..."}
	•	No inline CSS.
	•	Use semantic HTML (main, section, header, footer).

⸻

## 3. CSS Structure
	•	All styles must be external.
	•	Use variables.css for colors, radiuses, spacing, shadows, etc.
	•	Organize CSS by purpose: