# 🎨 Tenant Dashboard Theme & Design System

## Overview
This document outlines the comprehensive design system, color palette, typography, and styling used in the Maison Core tenant dashboard. The design follows modern UI/UX principles with a clean, professional aesthetic.

## 🎨 Color Palette

### Primary Colors
- **Primary Blue**: `#3b82f6` - Main brand color, buttons, links
- **Primary Dark**: `#1d4ed8` - Hover states, active elements
- **Primary Light**: `#dbeafe` - Backgrounds, subtle highlights

### Secondary Colors
- **Secondary Gray**: `#6b7280` - Secondary text, muted elements
- **Secondary Light**: `#f3f4f6` - Light backgrounds, borders
- **Secondary Dark**: `#374151` - Dark text, strong elements

### Status Colors
- **Success Green**: `#10b981` - Success states, completed items
- **Warning Yellow**: `#f59e0b` - Warning states, pending items
- **Error Red**: `#ef4444` - Error states, alerts
- **Info Blue**: `#3b82f6` - Information states, neutral items

### Neutral Colors
- **White**: `#ffffff` - Primary backgrounds, cards
- **Black**: `#000000` - Text, icons, strong elements
- **Light Gray**: `#f8fafc` - Subtle backgrounds, info boxes
- **Border Gray**: `#e2e8f0` - Card borders, dividers
- **Muted Gray**: `#9ca3af` - Disabled states, subtle text

### Semantic Colors
- **Verified Green**: `#10b981` - Verification status
- **Pending Yellow**: `#f59e0b` - Pending verification
- **Active Green**: `#10b981` - Active status
- **Inactive Gray**: `#6b7280` - Inactive status

## 🔤 Typography

### Font Family
- **Primary**: System fonts (San Francisco, Segoe UI, Roboto)
- **Fallback**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

### Font Sizes
- **Heading 1**: `32px` - Main page titles
- **Heading 2**: `24px` - Section headers
- **Heading 3**: `20px` - Card titles
- **Heading 4**: `16px` - Subsection headers
- **Heading 5**: `14px` - Small headers
- **Body Large**: `16px` - Main content text
- **Body**: `14px` - Standard text
- **Body Small**: `12px` - Secondary text, labels
- **Caption**: `11px` - Meta information, timestamps

### Font Weights
- **Light**: `300` - Subtle text
- **Regular**: `400` - Body text
- **Medium**: `500` - Labels, emphasis
- **Semi-bold**: `600` - Headers, important text
- **Bold**: `700` - Strong emphasis

### Line Heights
- **Tight**: `1.2` - Headers
- **Normal**: `1.4` - Body text
- **Relaxed**: `1.6` - Long content

## 🎭 Component Styles

### Cards
```css
.bw-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Buttons
```css
.bw-btn {
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.bw-btn-outline {
  background: transparent;
  color: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
}
```

### Form Elements
```css
.bw-input {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  color: #374151;
  background: #ffffff;
  transition: border-color 0.2s ease;
}

.bw-input:focus {
  border-color: #3b82f6;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
```

### Tables
```css
.bw-table {
  width: 100%;
  border-collapse: collapse;
}

.bw-table-header {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  color: #374151;
}

.bw-table-row {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.bw-table-row:hover {
  background: #f9fafb;
}
```

## 🎨 Layout System

### Grid System
- **Container**: Max-width with responsive margins
- **Grid**: CSS Grid with flexible columns
- **Spacing**: Consistent 8px base unit system
- **Breakpoints**: Mobile-first responsive design

### Spacing Scale
- **4px**: Small gaps, tight spacing
- **8px**: Standard gaps, button padding
- **12px**: Medium spacing, form elements
- **16px**: Standard spacing, card padding
- **24px**: Large spacing, section margins
- **32px**: Extra large spacing, page margins

### Border Radius
- **Small**: `4px` - Buttons, inputs
- **Medium**: `6px` - Cards, larger elements
- **Large**: `8px` - Main cards, containers
- **Full**: `50%` - Avatars, circular elements

## 🎯 Interactive Elements

### Hover States
- **Buttons**: Darker shade, subtle shadow
- **Cards**: Slight elevation, border color change
- **Links**: Color change, underline
- **Table Rows**: Background color change

### Focus States
- **Inputs**: Blue border with subtle shadow
- **Buttons**: Enhanced border, shadow
- **Links**: Clear visual indication

### Loading States
- **Spinners**: Animated circular progress
- **Skeletons**: Placeholder content
- **Disabled**: Reduced opacity, cursor change

## 📱 Responsive Design

### Breakpoints
- **Mobile**: `320px - 768px`
- **Tablet**: `768px - 1024px`
- **Desktop**: `1024px+`

### Mobile Adaptations
- **Stacked Layout**: Single column grid
- **Touch Targets**: Minimum 44px height
- **Simplified Navigation**: Collapsible menus
- **Optimized Typography**: Readable font sizes

## 🎨 Icon System

### Icon Library
- **Primary**: Lucide React Icons
- **Sizes**: 16px, 20px, 24px, 32px
- **Colors**: Inherit from parent or custom
- **States**: Active, inactive, hover, focus

### Common Icons
- **Navigation**: ArrowLeft, ArrowRight, Home
- **Actions**: Plus, Edit, Trash2, Save
- **Status**: CheckCircle, XCircle, AlertCircle
- **Content**: Car, Users, Calendar, Settings

## 🎭 Animation & Transitions

### Duration
- **Fast**: `0.15s` - Hover effects
- **Normal**: `0.2s` - Standard transitions
- **Slow**: `0.3s` - Complex animations

### Easing
- **Standard**: `ease` - Default transitions
- **Smooth**: `ease-in-out` - Hover effects
- **Bounce**: `cubic-bezier(0.68, -0.55, 0.265, 1.55)` - Special effects

### Properties
- **Color**: Smooth color transitions
- **Transform**: Scale, translate, rotate
- **Opacity**: Fade in/out effects
- **Shadow**: Elevation changes

## 🎨 Accessibility

### Color Contrast
- **Text**: Minimum 4.5:1 ratio
- **Large Text**: Minimum 3:1 ratio
- **UI Elements**: Minimum 3:1 ratio

### Focus Management
- **Visible Focus**: Clear focus indicators
- **Logical Tab Order**: Intuitive navigation
- **Skip Links**: Quick access to main content

### Screen Reader Support
- **Semantic HTML**: Proper heading structure
- **Alt Text**: Descriptive image alternatives
- **ARIA Labels**: Enhanced element descriptions

## 📋 Usage Guidelines

### Color Application
1. **Primary**: Use for main actions, links, and brand elements
2. **Secondary**: Use for supporting content and subtle elements
3. **Status**: Use consistently for state indication
4. **Neutral**: Use for backgrounds, borders, and text

### Typography Rules
1. **Hierarchy**: Maintain clear visual hierarchy
2. **Readability**: Ensure sufficient contrast and size
3. **Consistency**: Use consistent font weights and sizes
4. **Spacing**: Maintain proper line height and margins

### Component Guidelines
1. **Consistency**: Use established patterns and styles
2. **Accessibility**: Ensure proper contrast and focus states
3. **Responsiveness**: Design for all screen sizes
4. **Performance**: Optimize animations and transitions

## 🔧 Customization

### CSS Variables
```css
:root {
  --bw-primary: #3b82f6;
  --bw-primary-dark: #1d4ed8;
  --bw-secondary: #6b7280;
  --bw-success: #10b981;
  --bw-warning: #f59e0b;
  --bw-error: #ef4444;
  --bw-border: #e2e8f0;
  --bw-background: #f8fafc;
}
```

### Theme Overrides
- **Custom Colors**: Override CSS variables
- **Component Styles**: Extend base classes
- **Layout Adjustments**: Modify grid and spacing
- **Typography Changes**: Update font families and sizes

## 📚 Resources

### Design Tools
- **Figma**: Design system and components
- **Storybook**: Component documentation
- **Chrome DevTools**: CSS inspection and debugging

### Documentation
- **Component Library**: Reusable UI components
- **Style Guide**: Visual design standards
- **Accessibility Guide**: WCAG compliance guidelines

---

*This theme system ensures consistency, accessibility, and maintainability across the Maison Core tenant dashboard. Follow these guidelines to maintain the design integrity and user experience.* 