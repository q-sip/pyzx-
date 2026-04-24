/* --- BOILERPLATE / PALETTE --- */
Define(COLOR_PALETTE, AsArray(#DD2222, #FB6E00, #FFC500, #720096, #5E4FA2, #3288BD, #66C2A5, #ABDDA4, #E6F598, #FEE08B, #D53E4F, #9E0142))
Define(COLOR_PALETTE_ITER, AsIterator(COLOR_PALETTE))
Define(RandomColor, Function(RGB(RandomInt(255), RandomInt(255), RandomInt(255))))
Define(GetNextColor, Function(Coalesce(Next(COLOR_PALETTE_ITER), RandomColor())))
Define(ColorByLabel, AsMap())
Define(GetColorByLabel, Function(labels, Coalesce(Get(ColorByLabel, labels), Set(ColorByLabel, labels, GetNextColor()))))
Define(JoinLabels, Function(labels, Join(Sort(labels), ":")))

/* --- BASELINE NODE STYLE --- */
@NodeStyle {
Define(COLOR, GetColorByLabel(JoinLabels(Labels(node))))

// Logic to determine type letter
Define(T_VAL, Property(node, "t"))
Define(TYPE_CHAR, If(Equals(T_VAL, 1), "z", If(Equals(T_VAL, 2), "x", If(Equals(T_VAL, 3), "h", "b"))))

size: 6
color: COLOR
color-hover: Darker(COLOR)
color-selected: Darker(COLOR)
border-width: 0.6
border-color: #1D1D1D
font-size: 3
font-color: #1D1D1D
shape: "dot"

// Display ID on the first line and Type:Phase on the second
label: Format("{}\n{}:{}", Property(node, "id"), TYPE_CHAR, Property(node, "phase"))
// Offset the text so it sits above the node center

}

/* --- PYZX OVERRIDES --- */
@NodeStyle Equals(Property(node, "t"), 1) {
color: #00ff00
color-hover: Darker(#00ff00)
color-selected: Darker(#00ff00)
}

@NodeStyle Equals(Property(node, "t"), 2) {
color: #ff0000
color-hover: Darker(#ff0000)
color-selected: Darker(#ff0000)
}

@NodeStyle Equals(Property(node, "t"), 3) {
color: #ffff00
color-hover: Darker(#ffff00)
color-selected: Darker(#ffff00)
shape: "square"
size: 5
}

@NodeStyle Equals(Property(node, "t"), 0) {
color: #a0a0a0
color-hover: Darker(#a0a0a0)
color-selected: Darker(#a0a0a0)
size: 4
}


@NodeStyle HasLabel(node, "Output") {
color: #1A1A1A // Near black for visibility
border-width: 1.2
color-hover: Darker(#1A1A1A)
color-selected: Darker(#1A1A1A)
}

/* --- BASELINE EDGE STYLE --- */
@EdgeStyle {
// Logic for edge types (e.g., standard vs Hadamard)
Define(ET_VAL, Property(edge, "t"))
Define(ETYPE_CHAR, If(Equals(ET_VAL, 2), "h", "s"))

color: #666666
color-hover: Darker(#666666)
color-selected: Darker(#666666)
width: 0.3
width-hover: 0.6
width-selected: 0.6
font-size: 3
font-color: #1D1D1D
arrow-size: 1
label: ETYPE_CHAR
}

@EdgeStyle Equals(Property(edge, "t"), 2) {
color: #0000ff
color-hover: Darker(#0000ff)
color-selected: Darker(#0000ff)
width: 0.5
}

@EdgeStyle Equals(Property(edge, "kala"), 1) {
color: #e7e7feff
width: 0
}
@NodeStyle Equals(Property(node, "kala"), 1) {
color: #fffdfdff // Near black for visibility
border-width: 0
size: 0
}

/* --- VIEW SETTINGS --- */
@ViewStyle {
view: "tree"
tree-orientation: "horizontal"
tree-node-gap: 70
tree-level-gap: 30
background-color: #FFFFFF00
}

// Code generated from graph layout options [4/15/2026, 8:13:17 PM]
@ViewStyle {
view: "tree"
tree-orientation: "horizontal"
tree-node-gap: 65
tree-level-gap: 60
background-color: #FFFFFF00
}
