# 微信 135 编辑器兼容内联样式规范

微信公众号渲染会完全剥离 `<style>` 标签与 CSS class，只保留 inline style。本规范所有样式必须内联，且不使用外联资源。

## 容器规则

- 每个内容块用 `<section>` 包裹，不使用外层 `<div>` 容器（微信会自动提供宽度约束）。
- 文末必须加 `<v2></v2>` 版本标记，否则 135 编辑器会触发旧版迁移、破坏排版。
- 不使用 `<script>`、`<style>`、外联 class、`position:fixed/absolute`、外部字体。
- 图片用占位区域，用户后续替换。

## 组件样式（直接复制 inline）

### 文章标题（H1）
```html
<section style="text-align:center;padding:24px 16px 8px;">
  <h1 style="font-size:22px;font-weight:700;color:#1a3a5c;margin:0;line-height:1.4;">{{TITLE}}</h1>
</section>
```

### 章节小标题（H2，含 4px 色条）
```html
<section style="padding:18px 16px 6px;">
  <span style="display:inline-block;width:4px;height:17px;background:#1a3a5c;margin-right:8px;vertical-align:middle;"></span><strong style="font-size:17px;font-weight:700;color:#1a3a5c;vertical-align:middle;">{{HEADING}}</strong>
</section>
```

### 正文段落
```html
<section style="padding:6px 16px;">
  <p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 12px;">{{PARAGRAPH}}</p>
</section>
```

### 关键判断句（加粗着色）
```html
<strong style="color:#1a3a5c;">{{KEY_JUDGMENT}}</strong>
```

### 引用块
```html
<section style="padding:10px 16px;">
  <p style="font-size:15px;line-height:1.8;color:#555;background:#f5f7fa;padding:12px 14px;margin:0;border-radius:6px;">{{QUOTE}}</p>
</section>
```

### 列表项
```html
<section style="padding:4px 16px;">
  <p style="font-size:16px;line-height:1.8;color:#333;margin:0 0 8px;"><span style="color:#1a3a5c;margin-right:6px;">•</span>{{ITEM}}</p>
</section>
```

### 表格（深蓝表头白字 + 斑马纹）
```html
<section style="padding:8px 16px;overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;font-size:14px;line-height:1.6;">
    <thead>
      <tr style="background:#1a3a5c;color:#fff;">
        <th style="padding:8px 10px;text-align:left;border:1px solid #1a3a5c;">{{H1}}</th>
        <th style="padding:8px 10px;text-align:left;border:1px solid #1a3a5c;">{{H2}}</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#fff;"><td style="padding:8px 10px;border:1px solid #ddd;">{{C1}}</td><td style="padding:8px 10px;border:1px solid #ddd;">{{C2}}</td></tr>
      <tr style="background:#f5f7fa;"><td style="padding:8px 10px;border:1px solid #ddd;">{{C1}}</td><td style="padding:8px 10px;border:1px solid #ddd;">{{C2}}</td></tr>
    </tbody>
  </table>
</section>
```

## 风格禁忌

- 不使用科技电路风、发光、数字网格、渐变背景。
- 不堆砌 emoji；分隔用 `<section style="height:1px;background:#eee;margin:12px 16px;"></section>` 而非 `<hr>`（更可控）。
- 全部颜色取自深普鲁士蓝 `#1a3a5c` 与中性灰 `#333/#555/#ddd/#f5f7fa`，保持克制。
