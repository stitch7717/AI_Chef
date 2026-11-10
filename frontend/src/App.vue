<template>
  <router-view />
</template>

<style>
/* ============ 全局设计系统「Orea 蓝白极简」 ============ */
:root {
  /* 主按钮/强调：深黑蓝（Orea 的黑色按钮） */
  --brand-700: #101b31;
  --brand-600: #1b2b4a;
  --brand-500: #2e4066;
  --brand-100: #d8e4f5;
  --brand-50: #e8f1fb;

  /* 中性色 */
  --ink-900: #1b2b4a;
  --ink-600: #5a6b85;
  --ink-400: #93a3bc;
  --ink-200: #e2eaf4;
  --ink-100: #f2f6fb;

  /* 表面：浅蓝底 + 纯白卡 */
  --surface: #e9f2fb;
  --card: #ffffff;

  /* Orea 多彩功能色（圆环/圆点用） */
  --c-green: #34c79a;   /* 碳水绿 */
  --c-blue: #3d7fff;    /* 脂肪蓝 */
  --c-orange: #fbb040;  /* 蛋白橙 */
  --c-flame: #f97066;   /* 热量红 */
  --c-purple: #9b8afb;  /* 紫 */

  /* 语义别名（视图沿用） */
  --fresh: #34c79a;
  --fresh-bg: #e6f8f1;
  --danger: #ef5350;

  /* Element Plus 主题：黑色按钮 + 浅蓝态 */
  --el-color-primary: #1b2b4a;
  --el-color-primary-light-3: #3a4c72;
  --el-color-primary-light-5: #637699;
  --el-color-primary-light-7: #c2cfe3;
  --el-color-primary-light-8: #d8e4f5;
  --el-color-primary-light-9: #e8f1fb;
  --el-color-primary-dark-2: #101b31;
  --el-border-radius-base: 12px;
  --el-font-family: "PingFang SC", "HarmonyOS Sans SC", "Microsoft YaHei", sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
body {
  font-family: var(--el-font-family);
  color: var(--ink-900);
  background: linear-gradient(180deg, #edf4fc 0%, #e2edf9 100%) fixed;
  -webkit-font-smoothing: antialiased;
}

/* 滚动条 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #c7d5e6; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #93a3bc; }
::-webkit-scrollbar-track { background: transparent; }

/* 通用页面容器 */
.page-shell { padding: 28px 32px; max-width: 1200px; margin: 0 auto; }
.page-title { font-size: 24px; font-weight: 800; color: var(--ink-900); letter-spacing: .5px; }
.page-sub { font-size: 13px; color: var(--ink-400); margin-top: 4px; }

/* 白卡通用质感 */
.orea-card {
  background: var(--card); border-radius: 20px;
  box-shadow: 0 4px 20px rgba(27, 43, 74, .07);
}

/* 移动端对话框自适应（固定宽度会溢出小屏） */
@media (max-width: 768px) {
  .el-dialog { width: 92vw !important; margin-top: 8vh !important; }
  .el-message-box { width: 88vw !important; }
  .el-drawer__body { padding: 12px 14px !important; }
}

/* 移动端对话框自适应（固定宽度会溢出小屏） */
@media (max-width: 768px) {
  .el-dialog { width: 92vw !important; margin-top: 8vh !important; }
  .el-message-box { width: 88vw !important; }
  .el-drawer__body { padding: 12px 14px !important; }
}

/* 食材联想下拉（teleport 到 body，需全局样式） */
.ing-popper .ing-sug { display: flex; align-items: center; gap: 10px; padding: 3px 0; }
.ing-popper .ing-sug-img {
  width: 34px; height: 34px; border-radius: 9px; object-fit: cover;
  background: #f2f6fb; flex-shrink: 0; display: block;
}
.ing-popper .ing-sug-ph { display: flex; align-items: center; justify-content: center; font-size: 17px; }
.ing-popper .ing-sug-meta { display: flex; flex-direction: column; line-height: 1.3; min-width: 0; }
.ing-popper .ing-sug-meta b { font-size: 13.5px; color: #1b2b4a; }
.ing-popper .ing-sug-meta small { font-size: 11px; color: #93a3bc; }
.ing-popper li { padding: 6px 10px !important; height: auto !important; line-height: 1.3 !important; }

/* 食材联想下拉（teleport 到 body，需全局样式） */
.ing-popper .ing-sug { display: flex; align-items: center; gap: 10px; padding: 3px 0; }
.ing-popper .ing-sug-img {
  width: 34px; height: 34px; border-radius: 9px; object-fit: cover;
  background: #f2f6fb; flex-shrink: 0; display: block;
}
.ing-popper .ing-sug-ph { display: flex; align-items: center; justify-content: center; font-size: 17px; }
.ing-popper .ing-sug-meta { display: flex; flex-direction: column; line-height: 1.3; min-width: 0; }
.ing-popper .ing-sug-meta b { font-size: 13.5px; color: #1b2b4a; }
.ing-popper .ing-sug-meta small { font-size: 11px; color: #93a3bc; }
.ing-popper li { padding: 6px 10px !important; height: auto !important; line-height: 1.3 !important; }

/* 主按钮：深黑蓝 */
.el-button--primary {
  --el-button-bg-color: #1b2b4a;
  --el-button-border-color: #1b2b4a;
  --el-button-hover-bg-color: #2e4066;
  --el-button-hover-border-color: #2e4066;
  font-weight: 600;
}
</style>
