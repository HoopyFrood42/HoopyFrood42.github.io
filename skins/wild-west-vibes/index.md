---
layout: default
id: wild-west-vibes
title: Wild West Vibes
description: Western-themed AO3 work skin featuring custom SVG assets and vintage
  typography.
category: workskin
version: 1.0.0
tags:
- western
- vintage
- decorative
svgs:
- id: divider
  title: Chapter Divider
  file: divider.svg
  description: Thematic Western rope & cactus chapter divider
- id: icon
  title: Corner Accent Icon
  file: icon.svg
  description: Western star badge accent
- id: category-general
  title: Category General
  file: category-general.svg
  description: Wild West Vibes category general asset
---

# Wild West Vibes

A Western-themed AO3 work skin featuring custom SVG assets, stylized headers, and thematic chapter dividers.

---

## SVG Assets

Add your `.svg` files directly to the `skins/wild-west-vibes/` folder. Once pushed to GitHub, each SVG will be available at its own direct URL:

```text
https://hoopyfrood42.github.io/skins/wild-west-vibes/<filename>.svg
```

### Asset List

<!-- Once you add your SVGs, update this section with previews and direct links -->
*SVGs coming soon! Placeholders below show how to reference them:*

- **Chapter Divider:**
  - Direct URL: `https://hoopyfrood42.github.io/skins/wild-west-vibes/divider.svg`
  - Markdown preview: `![Divider](./divider.svg)`

- **Corner Accent / Icon:**
  - Direct URL: `https://hoopyfrood42.github.io/skins/wild-west-vibes/icon.svg`
  - Markdown preview: `![Icon](./icon.svg)`

---

## AO3 CSS Code

Copy and paste this CSS into your AO3 Work Skin:

```css
#workskin .wild-west-header {
  font-family: Georgia, serif;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 2px;
}

#workskin .wild-west-divider {
  display: block;
  width: 100%;
  height: 40px;
  background-image: url("https://hoopyfrood42.github.io/skins/wild-west-vibes/divider.svg");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  margin: 2em 0;
}
```

---

## How to Use on AO3

1. Go to **Dashboard > Skins > Work Skins > Create Work Skin**.
2. Give it a title (e.g. `Wild West Vibes`).
3. Paste the CSS above into the **CSS** field and click **Submit**.
4. When editing your work, go to **Associations > Select Work Skin** and choose `Wild West Vibes`.
5. In your work text (HTML mode), use your classes:
   ```html
   <p class="wild-west-divider"></p>
   ```

---

[← Back to Skins Directory](/skins/) | [Home](/)

