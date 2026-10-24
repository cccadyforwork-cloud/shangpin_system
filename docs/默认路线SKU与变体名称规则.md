# 默认上品路线：SKU 品名段与变体名称

适用于今后新建的默认上品工作台项目。已有 SKU、供应商明确提供的 SKU 和已上传记录不得自动改名；如需改动，应由用户确认并同步更新父子体关联。批量快速路线已有相同的英文品名段规则，见 `docs/batch_fast_prelisting.md`。

## 父子体 SKU 的品名段

- 父体和所有子体使用完全相同的英文品名段。
- 品名段最多取两个有意义的英文单词；每个单词首字母大写，其余字母小写，两个词直接连接，中间不加空格或横线。例如 `Mop Pad` → `MopPad`。
- 店铺前缀与品名段、品名段与变体属性之间可以保留 SKU 分隔符 `-`；“中间不加 `-`”只针对品名段内部。例如父体 `TTCA-MopPad`，子体 `TTCA-MopPad-Pink-2P`。
- 不在父体 SKU 末尾额外加 `-P` 或 `-PARENT`。子体颜色词各自仅首字母大写；混色 SKU 把颜色词直接拼接为 `GreenWhite`，展示名仍写 `Green+White`。数量后缀采用 `2P`、`4P` 等，不再用 `2PK`。例如 `TTCA-MopPad-GreenWhite-2P`。

## 变体完整名称

- 对 `COLOR/NUMBER_OF_ITEMS` 主题，内部预览和项目记录采用 `颜色, N Pack`，数字与 `Pack` 之间必须有一个空格，例如 `Pink, 2 Pack`。
- 单色首字母大写；不同颜色的组合用 `+` 连接、每个颜色首字母大写，例如 `Green+White, 2 Pack`。不写成 `Green-White` 或 `Green & White`。
- 若同一套装中不同颜色的材质也不同，内部完整预览名在各颜色后紧接括号标注已确认的材质，例如 `Green(Chenille)+White(Braided Cloth), 2 Pack`。材质标注只属于内部预览与项目说明，不挤入 Amazon 模板的 `Color` 字段。
- Amazon 原始模板的 `Color` 和 `Number of Items` 是两个独立字段：前者填写 `Pink`、`Green+White` 等颜色值，后者只填数字 `2`、`4` 等。`Pink, 2 Pack` 是供工作台和人工核对的完整预览名，不是模板中额外存在的字段，也不保证 Amazon 前台将两个选项合并成完全相同的一段文字。
