It's easy to extract simple extractable fields by using just xpath & some xml stuff, for example:

## Normal label, descriptions:
Using xpath like

```xpath
//[self::label or self::description]/..
```
is already good enough. You could also add  
`[preceding-sibling::defName or following-sibling::defName]` or  
`/..[not(@Abstract) or (@Abstract != "True" and @Abstract != "true")]`  
to ensure it's a non-abstract node


## For label & description in lists:

```xml
<HediffDef>
	<defName>AlcoholHigh</defName>
	<label>alcohol</label>
	<labelNoun>drunkenness</labelNoun>
	<description>Alcohol in the bloodstream. It makes people happy, but reduces capacities.</description>
	<stages>
		<li>
			<label>warm</label>
			<painFactor>0.9</painFactor>
			...
		</li>
		<li>
			<minSeverity>0.25</minSeverity>
			<label>tipsy</label>
			<painFactor>0.8</painFactor>
			...
		</li>
		<li>
			<minSeverity>0.4</minSeverity>
			<label>drunk</label>
			<painFactor>0.5</painFactor>
			...
		</li>
		<li>
			<minSeverity>0.7</minSeverity>
			<label>hammered</label>
			<painFactor>0.3</painFactor>
			...
		</li>
		<li>
			<minSeverity>0.9</minSeverity>
			<label>blackout</label>
			<painFactor>0.1</painFactor>
			...
		</li>
	</stages>
</HediffDef>
```
we could first locate where is the label, then search for its parent until we find XXXDef, and build a key from there:  
**label(warm)->li->stages->HediffDef** ====> **HediffDef.defName(AlcoholHigh)->stages->label.text(warm)->label** ====> **AlcoholHigh.stages.warm.label**  
  
if there's whitespace in between, just replace them with '_' and you're done.


There are other circumstances, such as multiple stages share the same label, or the label itself contains formatted strings:
```xml
<HediffDef>
<defName>Hypothermia</defName>
<label>hypothermia</label>
<description>Dangerously low core body temperature. Unless re-warmed, hypothermia gets worse and ends in death. Recovery is quick once the victim is re-warmed. Avoid hypothermia by wearing warm clothes in cold environments.</description>
<stages>
	<li>
		<label>shivering</label>
		<becomeVisible>false</becomeVisible>
	</li>
	<li>
		<label>shivering</label>
		<minSeverity>0.04</minSeverity>
	</li>
	<li>
		<capacity>Manipulation</capacity>
		<offset>-0.08</offset>
	</li>
	<li>
		<capacity>Consciousness</capacity>
		<offset>-0.05</offset>
	</li>
	...
</HediffDef>

<ThoughtDef>
	<defName>DeadMansApparel</defName>
	<workerClass>ThoughtWorker_DeadMansApparel</workerClass>
	<validWhileDespawned>true</validWhileDespawned>
	<stages>
		<li>
			<label>tainted {0}</label>
			<description>I am wearing a piece of apparel that someone died in. It creeps me out and feels dirty.</description>
		</li>
		<li>
			<label>tainted {0} (+1)</label>
			<description>I am wearing two pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
		</li>
		<li>
			<label>tainted {0} (+2)</label>
			<description>I am wearing three pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
		</li>
		<li>
			<label>tainted {0} etc</label>
			<description>I am wearing four or more pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
		</li>
	</stages>
</ThoughtDef>
```
This is why we also need to maintain a variable for their index when parsing, so that when multiple items are sharing an identical label, we can detect and auto-rename it to label-[index], making them  
**Hypothermia.stages.shivering-1.label & Hypothermia.stages.shivering-2.label** and  
**DeadMansApparel.stages.tainted.label & DeadMansApparel.stages.tainted-1.label** respectively.




## More complexed situation (QuestScriptDef)

WIP