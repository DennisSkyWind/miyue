-- 展平所有 Div（去掉嵌套 div 包裹），使 pandoc 能按标题层级切章
-- 用法: pandoc ... --lua-filter=flatten_div.lua
local function flatten_blocks(blocks)
  local out = {}
  for _, b in ipairs(blocks) do
    if b.t == "Div" then
      -- 展平内容，但保留 div 的 class 对应的语义标记（如 book/section -> 用 Div 保留会阻止切章）
      local inner = flatten_blocks(b.content)
      for _, ib in ipairs(inner) do
        out[#out + 1] = ib
      end
    else
      out[#out + 1] = b
    end
  end
  return out
end

function Pandoc(doc)
  doc.blocks = flatten_blocks(doc.blocks)
  return doc
end
