# Calnio Jinja2 Template System

## Overview

This document explains the Jinja2 template structure and CSS organization for the Calnio application.

## Template Structure

### Base Template (`base.html`)

The root template that provides the core HTML structure and is extended by all pages.

**Features:**
- Common `<head>` section with meta tags
- Analytics scripts (CrazyEgg, Plausible)
- Font and CSS imports
- Blocks for customization: `title`, `body_class`, `navbar`, `content`, `footer`, `extra_css`, `extra_js`

**Usage:**
```jinja2
{% extends "base.html" %}

{% block title %}Your Page Title{% endblock %}

{% block content %}
    <!-- Your page content -->
{% endblock %}
```

### Components

Reusable template components located in `templates/components/`:

#### `navbar.html`
- Responsive navigation header
- Desktop and mobile menus
- Hamburger menu animation
- Includes JavaScript for menu interactions

**Used by:** Landing page and other public pages

#### `footer.html`
- Company information
- Links to legal pages
- Version information and copyright

**Used by:** Landing page and other public pages

### Page Templates

#### `landing.html`
- **Extends:** `base.html`
- **Includes:** navbar, footer
- **CSS:** `landing.css`
- **Sections:**
  - Hero section with CTA buttons
  - "How it Works" (3 steps)
  - Features showcase
  - Integrations display
  - Pricing plans
  - Footer

#### `dashboard.html`
- **Extends:** `base.html`
- **Overrides:** navbar, footer (uses sidebar navigation)
- **CSS:** `dashboard.css`
- **Features:**
  - Sidebar navigation
  - Mobile responsive header
  - User profile settings
  - Tasks display
  - Form handling

#### `login.html`
- **Extends:** `base.html`
- **Overrides:** navbar, footer (minimal layout)
- **CSS:** `auth.css`
- **Features:**
  - Email/password login
  - Social authentication buttons
  - Link to signup page
  - Error message display

#### `signup.html`
- **Extends:** `base.html`
- **Overrides:** navbar, footer (minimal layout)
- **CSS:** `auth.css`
- **Features:**
  - User registration form
  - Password confirmation validation
  - Social authentication buttons
  - Link to login page

## CSS Architecture

### Variables (`variables.css`)

Centralized CSS custom properties for theming:

```css
:root {
  /* Primary Colors */
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  
  /* Background Colors */
  --bg-primary: #ffffff;
  --bg-secondary: #f9f9f9;
  
  /* Text Colors */
  --text-primary: #000000;
  --text-secondary: #292929;
  
  /* Spacing */
  --spacing-xs: 8px;
  --spacing-sm: 12px;
  --spacing-md: 16px;
  
  /* Typography */
  --font-family-primary: "Roboto", sans-serif;
  --font-size-base: 16px;
  
  /* Shadows */
  --shadow-card: 0 0 24px -6px rgba(147, 147, 147, 0.25);
  
  /* Border Radius */
  --radius-lg: 12px;
  
  /* Transitions */
  --transition-fast: 0.3s ease;
}
```

### Base Styles (`base.css`)

Global styles and resets:
- CSS reset (`*, margin, padding, box-sizing`)
- Body defaults
- Custom scrollbar styling
- Utility classes
- Container styles
- Responsive breakpoints
- Accessibility (focus states, reduced motion)

### Page-Specific CSS

#### `landing.css`
- Hero section styles
- Grid layouts for features
- Pricing card styles
- CTA button styles
- All landing page sections
- Mobile responsive adjustments

#### `dashboard.css`
- Sidebar navigation styles
- Mobile menu styles
- Card shadows and hovers
- Form input styles
- Dashboard-specific utilities
- Tailwind-like utility classes

#### `auth.css`
- Login/signup form styles
- Input field styling
- Social login buttons
- Error message display
- Centered card layout
- Animation effects

## Block System

### Available Blocks in `base.html`

1. **`title`** - Page title in `<title>` tag
2. **`body_class`** - CSS classes for `<body>` element
3. **`extra_css`** - Additional CSS files
4. **`navbar`** - Navigation header component
5. **`content`** - Main page content
6. **`footer`** - Footer component
7. **`extra_js`** - Additional JavaScript

### Example: Overriding Blocks

```jinja2
{% extends "base.html" %}

{% block title %}Custom Page Title{% endblock %}

{% block body_class %}custom-body-class another-class{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/custom.css" />
{% endblock %}

{% block navbar %}
<!-- Custom navigation or empty for no navbar -->
{% endblock %}

{% block content %}
<div class="container">
    <h1>Page Content</h1>
</div>
{% endblock %}

{% block footer %}
<!-- Custom footer or empty for no footer -->
{% endblock %}

{% block extra_js %}
<script>
    // Custom JavaScript
</script>
{% endblock %}
```

## Responsive Design

All templates follow a mobile-first approach:

### Breakpoints
- **Small (sm)**: 640px and up
- **Medium (md)**: 768px and up
- **Large (lg)**: 1024px and up

### Mobile Optimizations
- Touch-friendly button sizes (min 44x44px)
- Hamburger menus for mobile navigation
- Flexible grid layouts
- Optimized font sizes
- Responsive spacing

## Accessibility Features

1. **Keyboard Navigation**
   - Focus states on all interactive elements
   - Escape key closes mobile menus
   - Tab order preservation

2. **ARIA Labels**
   - Proper `aria-label` on icon buttons
   - Semantic HTML structure

3. **Reduced Motion**
   - Respects `prefers-reduced-motion` media query
   - Disables animations when requested

4. **High Contrast**
   - Supports `prefers-contrast: high` mode
   - Enhanced border colors

## Adding a New Page

1. Create template file in `templates/`:
```jinja2
{% extends "base.html" %}

{% block title %}New Page{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/newpage.css" />
{% endblock %}

{% block content %}
    <!-- Your content -->
{% endblock %}
```

2. Create CSS file in `static/css/`:
```css
/* ===== NEW PAGE STYLES ===== */

/* Import variables */
@import url("variables.css");

.newpage-specific-class {
  color: var(--primary);
  padding: var(--spacing-md);
}
```

3. Register route in FastAPI backend

## Best Practices

1. **Use CSS Variables** - Always prefer CSS variables for colors, spacing, etc.
2. **No Inline Styles** - All styling should be in external CSS files
3. **Semantic HTML** - Use proper HTML5 elements
4. **Component Reuse** - Create reusable components for repeated UI elements
5. **Mobile First** - Design for mobile, then enhance for desktop
6. **Accessibility** - Include proper ARIA labels and keyboard navigation
7. **DRY Principle** - Don't repeat yourself, use template inheritance

## File Organization

```
frontend/
├── templates/
│   ├── base.html                 # Root template
│   ├── landing.html             # Landing page
│   ├── dashboard.html           # Dashboard
│   ├── login.html              # Login page
│   ├── signup.html             # Signup page
│   └── components/
│       ├── navbar.html         # Navigation component
│       └── footer.html         # Footer component
│
└── static/
    └── css/
        ├── variables.css       # CSS variables
        ├── base.css           # Global styles
        ├── landing.css        # Landing page
        ├── dashboard.css      # Dashboard
        ├── auth.css          # Login/signup
        ├── layout.css        # Layout utilities (existing)
        └── components.css    # Component styles (existing)
```

## Maintenance

### Updating CSS Variables
To change the theme colors, shadows, spacing, etc., edit `variables.css`:

```css
:root {
  --primary: #new-color;      /* Updates all primary color usage */
  --spacing-md: 20px;          /* Updates all medium spacing */
}
```

### Adding New Components
1. Create component file in `templates/components/`
2. Include in parent template: `{% include "components/new.html" %}`
3. Add component-specific styles in CSS file

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox
- CSS Custom Properties (Variables)
- ES6+ JavaScript

## Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [CSS Variables Guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
