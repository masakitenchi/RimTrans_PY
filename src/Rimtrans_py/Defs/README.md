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
  
if there's whitespace in between, just replace them with `_` and you're done.  
P.S. there are also `\'` s in label. Replace them with "", otherwise the tag is invalid.

There are other circumstances, such as multiple stages sharing the same label, or the label itself contains formatted strings:

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
    </li> ...
  </stages>
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
**Hypothermia.stages.shivering-0.label & Hypothermia.stages.shivering-1.label** and  
**DeadMansApparel.stages.tainted.label & DeadMansApparel.stages.tainted-1.label** respectively.

## More complexed situation (QuestScriptDef)

I believe this would cover 99% of the translations, but the most complex system is still waiting for us.
Yes, it's QuestScriptDef.

Unlike other "rather static" Defs, QuestScriptDefs are basically "Tynan-script" written in xml.

Take a look at Script_TradeRequest.xml:

```xml
<QuestScriptDef>
  <defName>TradeRequest</defName>
  <questNameRules>
    <rulesStrings>
      <li>questName->Caravan to [settlement_label]</li>
      <li>questName->Trade with [settlement_label]</li>
      <li>questName->Selling to [settlement_label]</li>
      <li>questName->Supplies for [settlement_label]</li>
      <li>questName->A [special] [trade]</li>
      <li>special->Special</li>
      <li>special->Unique</li>
      <li>special->Non-traditional</li>
      <li>trade->Trade</li>
      <li>trade->Exchange</li>
      <li>trade->Deal</li>
      <li>trade->Offer</li>
    </rulesStrings>
  </questNameRules>
  <questDescriptionRules>
    <rulesStrings>
      <li>questDescription->A nearby settlement, [settlement_label], has a special trade request.
        They would like to purchase:
        \n [requestedThingCount]x [requestedThing_label] [qualityInfo](worth
        [requestedThingMarketValue_money])
        \nIf you want to make the trade, send a caravan with the requested items. The estimated
        travel time is [estimatedTravelTime_duration].</li>
      <li>qualityInfo(requestedThingHasQuality==True,priority=1)->of normal+ quality </li>
      <li>qualityInfo-></li>
    </rulesStrings>
  </questDescriptionRules>
  <root Class="QuestNode_Sequence">
    <nodes> ... <li Class="QuestNode_Letter">
        <inSignal>faction.BecameHostileToPlayer</inSignal>
        <label TKey="LetterLabelQuestFailed">Quest failed: [resolvedQuestName]</label>
        <text TKey="LetterTextQuestFailed">[faction_name] became hostile to you.</text>
      </li>
      ... <nodeIfChosenPawnSignalUsed Class="QuestNode_Letter">
        <letterDef>ChoosePawn</letterDef>
        <label TKey="LetterLabelFavorReceiver">[asker_faction_royalFavorLabel]</label>
        <text TKey="LetterTextFavorReceiver">Who should be credited with
      [asker_faction_royalFavorLabel] for fulfilling the trade request?</text>
        <chosenPawnSignal>ChosenPawnForReward</chosenPawnSignal>
        <useColonistsFromCaravanArg>true</useColonistsFromCaravanArg>
      </nodeIfChosenPawnSignalUsed>
    </nodes>
  </root>
</QuestScriptDef>
```

See? You can barely tell how to extract translations from this Def if you are to suddenly ordered to do it. But if we take a look at the file game generated when cleaning translation files:

```xml
<LanguageData>
<!-- EN:
  <li>questDescription->A nearby settlement, [settlement_label], has a special trade request. They
would like to purchase:\n\n  [requestedThingCount]x [requestedThing_label] [qualityInfo](worth
[requestedThingMarketValue_money])\n\nIf you want to make the trade, send a caravan with the
requested items. The estimated travel time is [estimatedTravelTime_duration].</li>
  <li>qualityInfo(requestedThingHasQuality==True,priority=1)->of normal+ quality </li>
  <li>qualityInfo-></li>
-->
<TradeRequest.questDescriptionRules.rulesStrings>
  <li>questDescription->附近一个名叫 [settlement_label] 的聚落向我们发出了一场交易请求。 他们想采购以下物资：\n\n
    [requestedThingCount]x [qualityInfo] [requestedThing_label](价值：
    [requestedThingMarketValue_money])\n\n如果你同意这场交易，请派出一支携带相应物资的远行队前往目标地点。
    旅途预估时间约为：[estimatedTravelTime_duration]。</li>
  <li>qualityInfo(requestedThingHasQuality==True,priority=1)->一般品质以上</li>
  <li>qualityInfo-></li>
</TradeRequest.questDescriptionRules.rulesStrings>
<!-- EN:
  <li>questName->Caravan to [settlement_label]</li>
  <li>questName->Trade with [settlement_label]</li>
  <li>questName->Selling to [settlement_label]</li>
  <li>questName->Supplies for [settlement_label]</li>
  <li>questName->A [special] [trade]</li>
  <li>special->Special</li>
  <li>special->Unique</li>
  <li>special->Non-traditional</li>
  <li>trade->Trade</li>
  <li>trade->Exchange</li>
  <li>trade->Deal</li>
  <li>trade->Offer</li>
-->
<TradeRequest.questNameRules.rulesStrings>
  <li>questName->远行队前往[settlement_label]</li>
  <li>questName->与[settlement_label]交易</li>
  <li>questName->向[settlement_label]出售</li>
  <li>questName->补给[settlement_label]</li>
  <li>questName->一场[special][trade]</li>
  <li>special->特别的</li>
  <li>special->独一无二的</li>
  <li>special->非传统的</li>
  <li>trade->贸易</li>
  <li>trade->交换</li>
  <li>trade->交易</li>
  <li>trade->供应</li>
</TradeRequest.questNameRules.rulesStrings>
<!-- EN: Quest failed: [resolvedQuestName] -->
<TradeRequest.LetterLabelQuestFailed.slateRef>任务失败：[resolvedQuestName]</TradeRequest.LetterLabelQuestFailed.slateRef>
<!-- EN: [faction_name] became hostile to you. -->
<TradeRequest.LetterTextQuestFailed.slateRef>[faction_name]开始与你敌对了。</TradeRequest.LetterTextQuestFailed.slateRef>
<!-- EN: [asker_faction_royalFavorLabel] -->
<TradeRequest.LetterLabelFavorReceiver.slateRef>[asker_faction_royalFavorLabel]</TradeRequest.LetterLabelFavorReceiver.slateRef>
<!-- EN: Who should be credited with [asker_faction_royalFavorLabel] for fulfilling the trade
request? -->
<TradeRequest.LetterTextFavorReceiver.slateRef>谁应该作为[asker_faction_royalFavorLabel]以完成此次交易任务？</TradeRequest.LetterTextFavorReceiver.slateRef>
```

The pattern isn't that hard to tell, right?

It's still the old-schooly "build key string from the bottom up". But the final node could be either the name of the list itself (rulesStrings) or a new key we've never seen before: the

<h3 style="text-align: center;">slateRef</h3>.

WIP
