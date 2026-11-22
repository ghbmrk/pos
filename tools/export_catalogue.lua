-- Dump PoB game data that the catalogue needs as JSON on stdout.
-- usage: luajit tools/export_catalogue.lua <PoB src dir>
-- Loads Data/Gems.lua, Data/Skills/*.lua, Data/Bases/*.lua, Data/Uniques/*.lua directly (no PoB runtime).
-- SkillType ids are read from Data/Global.lua so that skill type names survive re-pins unchanged.
local src = assert(arg[1], "usage: export_catalogue.lua <PoB src dir>"):gsub("/$", "")

local function readfile(p) local f = assert(io.open(p, "rb")); local s = f:read("*a"); f:close(); return s end

local function esc(s)
  return '"' .. s:gsub('[%c"\\]', function(c)
    if c == '"' then return '\\"' elseif c == "\\" then return "\\\\" end
    return string.format("\\u%04x", c:byte())
  end) .. '"'
end

local function sorted_keys(t)
  local ks = {}
  for k in pairs(t) do ks[#ks + 1] = k end
  table.sort(ks, function(a, b)
    if type(a) == type(b) then return a < b end
    return type(a) == "number"
  end)
  return ks
end

local function enc(v)
  local t = type(v)
  if t == "string" then return esc(v)
  elseif t == "number" then
    if v ~= v or v == math.huge or v == -math.huge then return "null" end
    return string.format("%.14g", v)
  elseif t == "boolean" then return tostring(v)
  elseif t == "table" then
    if #v > 0 or next(v) == nil then
      local parts = {}
      for i = 1, #v do parts[i] = enc(v[i]) end
      return "[" .. table.concat(parts, ",") .. "]"
    end
    local parts = {}
    for _, k in ipairs(sorted_keys(v)) do parts[#parts + 1] = esc(tostring(k)) .. ":" .. enc(v[k]) end
    return "{" .. table.concat(parts, ",") .. "}"
  end
  return "null"
end

-- SkillType: name -> id, from Global.lua
local globalSrc = readfile(src .. "/Data/Global.lua")
local stText = assert(globalSrc:match("\nSkillType = (%b{})"), "SkillType table not found in Global.lua")
local SkillType = assert(loadstring("return " .. stText))()
local stName = {}
for k, v in pairs(SkillType) do stName[v] = k end
local function typeNames(list)
  if not list then return nil end
  local out = {}
  for i, id in ipairs(list) do out[i] = stName[id] or tostring(id) end
  return out
end

-- Gems
local gems = dofile(src .. "/Data/Gems.lua")

-- PoB generated data files come in two shapes across versions: `return function(a, b) ... end` or a body reading `local a, b = ...`.
-- Run either: pass the args to the chunk, and if it returns a function, call that with them too.
local function callGenerated(chunk, ...)
  local r = chunk(...)
  if type(r) == "function" then r(...) end
end

-- Skills (granted effects): files are `return function(skills, mod, flag, skill) ... end`
local stub = function() return {} end
local skills = {}
-- Any other PoB global the skill files touch (ModFlag, KeywordFlag, ...) is an inert proxy: only skill type data is read.
local proxy = {}
local function same() return proxy end
setmetatable(proxy, { __index = same, __call = same, __add = same, __sub = same, __mul = same, __concat = same })
local env = setmetatable({ SkillType = SkillType, bit = setmetatable({}, { __index = function() return function() return 0 end end }) }, { __index = function(_, k) local v = _G[k]; if v ~= nil then return v end return proxy end })
for _, f in ipairs({ "act_dex", "act_int", "act_str", "other", "sup_dex", "sup_int", "sup_str", "minion", "spectre" }) do
  local chunk = assert(loadfile(src .. "/Data/Skills/" .. f .. ".lua"))
  setfenv(chunk, env)
  callGenerated(chunk, skills, stub, stub, stub)
end

local outGems = {}
for gid, g in pairs(gems) do
  local s = skills[g.grantedEffectId]
  local isSupport = g.gemType == "Support"
  local e = {
    id = g.grantedEffectId, gem_id = gid, name = g.name, type = g.gemType,
    support = isSupport, tags = g.tagString, tier = g.Tier,
    req = { str = g.reqStr, dex = g.reqDex, int = g.reqInt },
    weapon = g.weaponRequirements,
  }
  if s then
    e.description = s.description
    e.skill_types = typeNames(s.skillTypes and (function()
      local l = {}; for id in pairs(s.skillTypes) do l[#l + 1] = id end; table.sort(l); return l end)())
    if isSupport then
      e.require_types = typeNames(s.requireSkillTypes)
      e.exclude_types = typeNames(s.excludeSkillTypes)
      e.add_types = typeNames(s.addSkillTypes)
      e.family = s.gemFamily
    end
    e.cast_time = s.castTime
    e.max_level = s.levels and #s.levels or nil
  else
    e.no_skill_data = true
  end
  outGems[#outGems + 1] = e
end
table.sort(outGems, function(a, b) return a.gem_id < b.gem_id end)

-- Bases
local bases = {}
local baseFiles = io.popen('ls "' .. src .. '/Data/Bases"')
for fn in baseFiles:lines() do
  if fn:match("%.lua$") then
    local t = {}
    callGenerated(assert(loadfile(src .. "/Data/Bases/" .. fn)), t)
    for name, b in pairs(t) do
      bases[#bases + 1] = {
        name = name, type = b.type, subtype = b.subType, tags = sorted_keys(b.tags or {}),
        implicit = b.implicit, req_level = b.req and b.req.level,
        armour = b.armour, weapon = b.weapon,
      }
    end
  end
end
baseFiles:close()
table.sort(bases, function(a, b) return a.name < b.name end)

-- Uniques: text blocks, line 1 = name, line 2 = base type, then header lines (Variant:, Implicits: N, ...), then mod lines.
-- Mod lines may carry `{variant:1,2}`, `{tags:...}`, `{range:..}` etc. prefixes; `{variant:}` is kept as `variants`, the rest dropped.
local HEADERS = { "Variant", "Implicits", "League", "Source", "Version", "Sockets", "Limited to", "Selected Variant",
  "Selected Alt Variant", "Has Alt Variant", "Radius", "Right ring slot", "Left ring slot", "Crafted", "Allow Duplicate Variants" }
local function isHeader(line)
  local key = line:match("^([%a ]+):")
  if not key then return false end
  key = key:gsub(" Two$", ""):gsub(" Three$", "")
  for _, h in ipairs(HEADERS) do if key == h then return true end end
  return false
end
local function parseUnique(block)
  local rows = {}
  for line in (block .. "\n"):gmatch("([^\n]*)\n") do
    line = line:gsub("\r$", "")
    if line:match("%S") then rows[#rows + 1] = line:gsub("^%s+", "") end
  end
  if #rows < 2 then return nil end
  local u = { name = rows[1], base = rows[2] }
  local variants, lines, nImplicit = {}, {}, 0
  for i = 3, #rows do
    local line = rows[i]
    local n = line:match("^Implicits:%s*(%d+)")
    if n then nImplicit = tonumber(n)
    elseif line:match("^Requires Level%s+%d+") then u.req_level = tonumber(line:match("%d+"))
    elseif line:match("^Variant:") then variants[#variants + 1] = line:match("^Variant:%s*(.-)%s*$")
    elseif not isHeader(line) then
      local vs
      while true do
        local tag = line:match("^(%b{})")
        if not tag then break end
        local v = tag:match("^{variant:([%d,]+)}$")
        if v then vs = {}; for d in v:gmatch("%d+") do vs[#vs + 1] = tonumber(d) end end
        line = line:sub(#tag + 1)
      end
      lines[#lines + 1] = { text = line, variants = vs }
    end
  end
  -- implicits are the first N mod lines
  for i, l in ipairs(lines) do if i <= nImplicit then l.implicit = true end end
  if #variants > 0 then u.variants = variants end
  u.lines = lines
  return u
end
local uniques = {}
local uf = io.popen('ls "' .. src .. '/Data/Uniques"')
for fn in uf:lines() do
  local slot = fn:match("^(.+)%.lua$")
  if slot then
    local list = dofile(src .. "/Data/Uniques/" .. fn)
    for _, block in ipairs(list) do
      local u = parseUnique(block)
      if u then u.file = slot; uniques[#uniques + 1] = u end
    end
  end
end
uf:close()
table.sort(uniques, function(a, b) if a.name ~= b.name then return a.name < b.name end return a.base < b.base end)

io.write(enc({ gems = outGems, bases = bases, uniques = uniques }))
