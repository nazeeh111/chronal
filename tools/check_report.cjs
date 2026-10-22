#!/usr/bin/env node
'use strict';
// Logic regression checks for trusted, locally generated CHRONAL HTML.
// Executes actual report functions with small dependency stubs, not a browser
// or a complete DOM. This does not test layout, event wiring or accessibility.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

if (process.argv.length !== 3) {
  console.error('Usage: node tools/check_report.cjs PATH/TO/TRUSTED/report.html');
  process.exit(2);
}
const html = fs.readFileSync(process.argv[2], 'utf8');
// Inspect actual static markup only, excluding JSON records and JS source strings.
const markup = html.split(/<script\b/i)[0];
const ids = [...markup.matchAll(/\bid=["']([^"']+)["']/g)].map(match => match[1]);
assert.equal(new Set(ids).size, ids.length, 'Duplicate static HTML IDs break native anchors and DOM lookups');
for (const target of [...markup.matchAll(/\bhref=["']#([^"']+)["']/g)].map(match => match[1])) {
  assert.equal(ids.filter(id => id === target).length, 1, 'Native anchor must have exactly one target: ' + target);
}
const sectionIds=[...markup.matchAll(/<section\b[^>]*\bid=["']([^"']+)["']/g)].map(match=>match[1]);
const headerNav=markup.match(/<nav\b[^>]*aria-label=["']Report sections["'][^>]*>([\s\S]*?)<\/nav>/)[1];
for(const id of sectionIds){
 assert.equal([...headerNav.matchAll(/href=["']#([^"']+)["']/g)].filter(match=>match[1]===id).length,1,'Every evidence section must be available through native and mobile navigation: '+id);
}
assert.match(markup, /<section\b[^>]*\bid=["']interval["']/i, 'Interval anchor must target its comparison section');
assert.match(markup, /<p\b[^>]*\bid=["']uncertainty-interval["']/i, 'Uncertainty explanation must have a distinct ID');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]);
const script = scripts.find(text => text.includes('function runCommand('));
assert.ok(script, 'CHRONAL command script not found');
// The report keeps these self-contained functions on individual source lines.
// Fail visibly if authoring changes this contract, rather than testing a copy.
const names = ['detailNumber', 'sessionLabel', 'account', 'setAssetFocus', 'selectAsset', 'fills', 'commandStatus', 'resolveSession', 'chooseSession', 'windowMetrics', 'setRange', 'applyRange', 'chartSessionFromX', 'navigateSection', 'activeFitIndex', 'selectFit', 'eventSlot', 'moveEvent', 'modelContext', 'executionContext', 'renderCommandChoices', 'showCommands', 'navigateLink', 'jumpSection', 'matchingIntents', 'inspectIntent', 'intentFinder', 'findAttempts', 'executeCommand', 'recallCommand', 'runCommand'];
assert.match(script,/document\.querySelectorAll\('header nav a'\).*addEventListener\('click',navigateLink\)/,'Header links use repeatable navigation');
assert.match(script,/\$\('section-jump'\)\.addEventListener\('change',jumpSection\)/,'Native section picker wired');
assert.match(script,/for\(const id of \['asset-focus','fill-asset','finder-asset'\]\).*setAssetFocus\(\$\(id\)\.value\)/,'All native asset controls share one setter');
const historyListener=script.split('\n').find(line=>line.includes("$('command').addEventListener('keydown'"));
assert.match(historyListener,/if\(e.isComposing\|\|!e.altKey\|\|e.ctrlKey\|\|e.metaKey\|\|e.shiftKey\)return/,'History must preserve unmodified arrows and composition');
const updateSource=script.split('\n').find(line=>line.startsWith('function update('));
assert.match(updateSource,/table\('events'.*sessionLabel\(e.index\)/,'Event rows must preserve intraday timestamps');
assert.match(updateSource,/sessionLabel\(f.test_start\).*sessionLabel\(f.test_end-1\).*sessionLabel\(f.train_end\)/,'Fold boundaries must preserve intraday timestamps');
const actualFunctions = names.map(name => {
  const line = script.split('\n').find(text => text.startsWith(`function ${name}(`));
  assert.ok(line && line.endsWith('}'), `Cannot extract complete ${name} function`);
  return line;
}).join('\n');

// Execute the actual source-day counter as well as the label helper. Fit cutoffs
// before the evaluated region must retain their intraday timestamp identity.
const dayCounter=script.split('\n').find(line=>line.includes('const dayCounts='));
assert.ok(dayCounter,'Source-date counter initialization not found');
const cutoffProbe=vm.runInNewContext(`let rangeEnd;const first={indices:[2,3]};const D={dates:['2024-01-01T09:00:00Z','2024-01-01T10:00:00Z','2024-01-02T09:00:00Z','2024-01-02T10:00:00Z']};const dateAt=i=>D.dates[i].slice(0,10);${dayCounter};${script.split('\n').find(line=>line.startsWith('function sessionLabel('))};sessionLabel(1)`,{}, {timeout:1000});
assert.equal(cutoffProbe,'2024-01-01T10:00:00Z','Pre-region intraday fit cutoff must retain source timestamp');

const scenario = `
const elements = {
  'fill-session-only': {checked:false}, 'fill-asset': {value: ''}, 'fill-side': {value: 'all'}, previous: {}, next: {},
  strategy: {value: 'candidate'}, view: {value: 'equity'}, session: {value: '0'},
  'session-date': {value: '2024-01-01'},
  performance: {scrollIntoView(options){assert.equal(options.block,'start'); scrolls.push('performance')}},
  risk: {scrollIntoView(options){assert.equal(options.block,'start'); scrolls.push('risk')}},
  interval: {scrollIntoView(options){assert.equal(options.block,'start'); scrolls.push('interval')}},
  account: {scrollIntoView(options){assert.equal(options.block,'start'); scrolls.push('account')}},
  command: {value:'', focus(){this.focused=true}}, 'help-dialog': {open: false, showModal(){this.open = true},close(){this.open=false}}
};
const node = () => ({children:[], value:'', listeners:{},focus(){this.focused=true},addEventListener(kind,callback){this.listeners[kind]=callback},querySelectorAll(){return []}, replaceChildren(...items){this.children=items}, append(...items){this.children.push(...items)}});
for(const id of ['model-fit','model-features','execution-metrics','intent-table','session-events','previous-event','next-event','finder-asset','finder-outcome','finder-reason','finder-table','finder-previous','finder-next','command-search','command-choices','section-jump','asset-focus','account-metrics'])elements[id]=node();
for(const id of ['model','execution','finder'])elements[id]={scrollIntoView(options){assert.equal(options.block,'start'); scrolls.push(id)}};
const focusCalls=[];
for(const id of ['performance','risk','interval','account','model','execution','finder']){
 elements[id].setAttribute=(name,value)=>{assert.equal(name,'tabindex');assert.equal(String(value),'-1')};
 elements[id].focus=options=>{assert.equal(options.preventScroll,true);assert.equal(scrolls.at(-1),id,'Focus follows the explicit destination scroll');focusCalls.push(id)};
}
const document={createElement:node};
const facts = (id,pairs) => {tables[id]=pairs};
const $ = key => { assert.ok(Object.hasOwn(elements, key), 'Unknown element ' + key); return elements[key] };
const num = String, money = String, pct=String, messages = {}, tables = {}, dayCounts = {}, scrolls = [];
let rangeStart = 0, rangeEnd = 1, renders = 0,intentPage=0,commandHistory=[],historyIndex=0,historyDraft='',assetFocus='';
const renderRange = () => {renders++};
let current = 'candidate', page = 0, rows = [], updates = 0, charts = 0, inspections = 0;
const text = (id, value) => {messages[id] = value};
const table = (id, headers, value) => {tables[id]=value;if(id==='fills')rows = value};
const update = () => {updates++}, chart = () => {charts++}, inspect = () => {inspections++};
const location = {hash: ''};
const dates = ['2024-01-01', '2024-01-02','2024-01-03'];
const dateAt = index => dates[index].slice(0,10);
// sessionLabel is extracted from the report below.
const makeFill = (asset, quantity) => ({index:0, asset, quantity, fill_time:'2024-01-01T09:00:00Z', price:20, commission:1, cash_after:200});
const simulation = {positions:[[11,22,33],[44,55,66]],indices:[0, 1], fills:[makeFill('all',1), makeFill('OTHER',2), makeFill('all',-3)], events:[]};
const commandOptions=['help','strategy candidate','strategy other','goto finder','view equity','find all'];
const D = {assets:['all','OTHER','Asset / with spaces'],ledger:{candidate:{sessions:[{},{}]},other:{sessions:[{},{}]}},dates,winner:'candidate', results:{candidate:{simulation}, other:{simulation}}};
${actualFunctions}
// Nonzero recorded quantities must remain visible at all supported magnitudes.
assert.equal(detailNumber(null),'—');
assert.equal(detailNumber(0),'0');
for(const value of [1e-12,-1e-12,0.004,-0.004,123456789,1.23456789]){
 const rendered=detailNumber(value);
 assert.notEqual(Number(rendered),0);
 assert.equal(Math.sign(Number(rendered)),Math.sign(value));
 assert.ok(Math.abs(Number(rendered)/value-1)<1e-7);
}
dates[0]='2024-01-01T09:00:00Z';dates[1]='2024-01-01T10:00:00Z';
dayCounts['2024-01-01']=2;
assert.equal(sessionLabel(0),'2024-01-01T09:00:00Z');
assert.equal(sessionLabel(1),'2024-01-01T10:00:00Z');
dates[0]='2024-01-01';dates[1]='2024-01-02';delete dayCounts['2024-01-01'];

fills(); assert.equal(rows.length, 3);
simulation.fills.push({...makeFill('TINY',-1e-12),price:0.0000004,commission:1e-10});
fills(); assert.equal(Number(rows.at(-1)[2]),-1e-12);
assert.equal(Number(rows.at(-1)[3]),4e-7); assert.equal(Number(rows.at(-1)[4]),1e-10);
simulation.fills.pop();

$('fill-asset').value = 'all'; fills();
assert.equal(rows.length, 2); assert.deepEqual(rows.map(row => row[1]), ['all','all']);
$('fill-side').value = 'buy'; fills(); assert.equal(rows.length, 1); assert.equal(rows[0][2], '1');
$('fill-side').value = 'sell'; fills(); assert.equal(rows.length, 1); assert.equal(rows[0][2], '-3');
$('fill-asset').value = 'OTHER'; fills(); assert.equal(rows.length, 0);
assert.equal(messages['page-info'], 'No matching fills');
assert.equal($('previous').disabled, true); assert.equal($('next').disabled, true);
$('fill-asset').value = ''; $('fill-side').value = 'all';
simulation.fills = Array.from({length:16}, () => makeFill('all',1));
page=0; fills(); assert.equal(rows.length, 15); assert.equal($('next').disabled, false);
page=1; fills(); assert.equal(rows.length, 1); assert.equal($('next').disabled, true);
assert.equal($('previous').disabled, false);

runCommand('strategy other'); assert.equal(current, 'other'); assert.equal(updates, 1);
assert.equal(D.winner, 'candidate');
runCommand('strategy missing'); assert.equal(current, 'other'); assert.equal(updates, 1);
runCommand('strategy __proto__'); assert.equal(current, 'other');
runCommand('view drawdown'); assert.equal($('view').value, 'drawdown'); assert.equal(charts, 1);
runCommand('view missing'); assert.equal(charts, 1);
runCommand('goto risk'); assert.equal(location.hash, 'risk');
runCommand('goto https://example.invalid'); assert.equal(location.hash, 'risk');
runCommand('session 2024-01-02'); assert.equal(Number($('session').value), 1); assert.equal(inspections, 1);
$('session-date').value = '2024-01-03'; runCommand('session 2024-01-03');
assert.equal($('session-date').value, '2024-01-02'); assert.equal(inspections, 1);
assert.match(messages['command-result'], /No evaluated session/);
// Actual interval helpers, independently calculated numeric expectations.
const metricSim = {initial_cash:100, equity:[110,99,108], indices:[10,20,30], fills:[
 {index:10,commission:1,quantity:2,price:10},
 {index:20,commission:3,quantity:-2,price:12},
 {index:30,commission:5,quantity:1,price:14}
]};
let metric = windowMetrics(metricSim,1,2);
assert.ok(Math.abs(metric.total_return-(108/110-1))<1e-12);
assert.ok(Math.abs(metric.max_drawdown+0.1)<1e-12);
assert.equal(metric.fees,8); assert.equal(metric.notional,38); assert.equal(metric.sessions,2);
metric=windowMetrics(metricSim,0,0);
assert.ok(Math.abs(metric.total_return-0.1)<1e-12);
assert.equal(metric.max_drawdown,0); assert.equal(metric.fees,1); assert.equal(metric.sessions,1);
metric=windowMetrics(metricSim,1,1);
assert.ok(Math.abs(metric.total_return+0.1)<1e-12);
assert.equal(metric.fees,3); assert.equal(metric.notional,24);
const noFills=windowMetrics({...metricSim, fills:[]},0,2);
assert.equal(noFills.fees,0); assert.equal(noFills.notional,0);
assert.ok(Math.abs(noFills.total_return-0.08)<1e-12);


// Failed intervals retain both endpoints and do not render partial state.
assert.equal(setRange(1,0),false); assert.equal(setRange(-1,1),false);
assert.equal(setRange(0,2),false); assert.equal(setRange(0.5,1),false);
assert.equal(rangeStart,0); assert.equal(rangeEnd,1); assert.equal(renders,0);
assert.equal(setRange(1,1),true); assert.equal(rangeStart,1); assert.equal(rangeEnd,1);
assert.equal(renders,1);
assert.equal(applyRange('#2','#1'),false); assert.equal(rangeStart,1); assert.equal(rangeEnd,1);
assert.equal(applyRange('#0','#2'),false); assert.equal(renders,1);
assert.equal(applyRange('#1','#2'),true); assert.equal(rangeStart,0); assert.equal(rangeEnd,1);
assert.equal(location.hash,'interval'); assert.equal(D.winner,'candidate');
assert.equal(resolveSession('#1').index,0); assert.equal(resolveSession('#2').index,1);
for(const token of ['#0','#3','#-1','#1.5','#9007199254740993','','nonsense'])assert.ok(resolveSession(token).error);
chooseSession(0); assert.equal(Number($('session').value),0);
for(const token of ['', 'bad-date', '2024-01-03']){
 $('session-date').value=token; runCommand('session '+token);
 assert.equal($('session-date').value,'2024-01-01'); assert.equal(Number($('session').value),0);
}
dates[1]='2024-01-01'; assert.match(resolveSession('2024-01-01').error,/Multiple sessions/);
runCommand('session #2'); assert.equal(Number($('session').value),1);
assert.equal(D.winner,'candidate'); dates[1]='2024-01-02';
assert.equal(chartSessionFromX(60,20),0); assert.equal(chartSessionFromX(975,20),19);
assert.equal(chartSessionFromX(-200,20),0); assert.equal(chartSessionFromX(2000,20),19);
assert.equal(chartSessionFromX(975,1),0);
for(let i=0;i<20;i++)assert.equal(chartSessionFromX(60+(i+1)/20*915,20),i);

runCommand('reset'); assert.equal(rangeStart,0); assert.equal(rangeEnd,1);
const scrollCount=scrolls.length;
navigateSection('interval'); navigateSection('interval');
assert.equal(location.hash,'interval'); assert.equal(scrolls.length,scrollCount+2);
assert.deepEqual(scrolls.slice(-2),['interval','interval']);assert.deepEqual(focusCalls.slice(-2),['interval','interval']);
// Recorded model/event inspection uses half-open fit chronology and exact session indices.
current='candidate'; simulation.indices=[0,1];
const model={kind:'ridge',fit_cutoff:'2023-12-31T00:00:00Z',sample_count:12,ridge_alpha:1,
 intercept:0.02,feature_names:['momentum'],feature_mean:[0.1],feature_scale:[0.2],coefficients:[0.3],
 feature_formula:'trailing only',label_formula:'future open label'};
const records=[{test_start:0,test_end:1,train_end:0,first_decision_session:0,model},
 {test_start:1,test_end:2,train_end:1,first_decision_session:1,model:{kind:'trend'}}];
D.results.candidate.fit_records=records; D.results.candidate.spec={name:'candidate',lookback:10};
assert.equal(activeFitIndex(records,0),0); assert.equal(activeFitIndex(records,1),1);
assert.equal(activeFitIndex(records,2),-1); assert.equal(activeFitIndex(records,-1),-1);
modelContext(0); assert.equal(tables['model-features'][0][0],'momentum');
assert.equal(tables['model-features'][0][3],Number(0.3).toPrecision(8));
assert.equal(messages['feature-formula'],'trailing only');
modelContext(1); assert.match(messages['model-note'],/no fitted regression/);
assert.equal($('model-features').children.length,0); assert.equal(messages['feature-formula'],'');
const saveStart=records[1].test_start; records[1].test_start=2; modelContext(1);
assert.match(messages['model-note'],/No recorded fit/); assert.equal($('model-fit').value,''); records[1].test_start=saveStart;
runCommand('fit #2'); assert.equal(Number($('session').value),1); assert.equal(location.hash,'model');
for(const command of ['fit #0','fit #3','fit #1.1','fit #9007199254740993']){
 runCommand(command); assert.equal(Number($('session').value),1);
}
assert.equal(D.winner,'candidate');
simulation.events=[{index:1,type:'z',details:'later'},{index:0,type:'a',details:'earlier'},{index:1,type:'duplicate',details:{reason:'cash'}}];
$('session').value=0; assert.equal(eventSlot(-1),-1); assert.equal(eventSlot(1),1);
runCommand('next-event'); assert.equal(Number($('session').value),1); assert.equal(location.hash,'execution');
const inspected=inspections; runCommand('next-event'); assert.equal(inspections,inspected); assert.match(messages['command-result'],/No later/);
runCommand('previous-event'); assert.equal(Number($('session').value),0);
simulation.intents=[{index:0,asset:'all',kind:'rebalance',requested_quantity:-3,capacity_limit:2,
 capacity_allowed_quantity:-2,cash_scale:null,cash_scaled_quantity:-2,filled_quantity:-1,expired_quantity:-2,outcome:'partial',reasons:['capacity']}];
D.execution_evidence={candidate:{sessions:[{fill_ordinals:[0],adverse_fill_cost:0.125,commission:0.25},{fill_ordinals:[],adverse_fill_cost:0,commission:0}]}};
executionContext(0); assert.equal(tables['intent-table'][0][1],'-3');
assert.equal(tables['intent-table'][0][6],'-1');assert.equal(tables['intent-table'][0][7],'-2');
assert.equal(tables['intent-table'][0][8],'partial / capacity');
assert.equal(tables['intent-table'][0][4],'Not applied');
simulation.intents[0].cash_scale=0; executionContext(0);
assert.equal(tables['intent-table'][0][4],'0');
simulation.intents[0].cash_scale=null;
assert.equal($('previous-event').disabled,true);assert.equal($('next-event').disabled,false);
$('session').value=1; executionContext(1); assert.equal($('intent-table').children.length,0);
assert.match(messages['execution-note'],/No matching request rows/);
simulation.events=[]; executionContext(1); assert.equal($('session-events').textContent,'No recorded events in this session.');
assert.equal($('previous-event').disabled,true);assert.equal($('next-event').disabled,true);
// Session, asset and side filters intersect and retain explicit no-match state.
simulation.fills=[makeFill('all',1),{...makeFill('all',-2),index:1},{...makeFill('OTHER',3),index:1}];
$('fill-session-only').checked=true; $('session').value=1; $('fill-asset').value='all'; $('fill-side').value='sell'; page=0;
fills();assert.equal(rows.length,1);assert.equal(rows[0][2],'-2');
$('session').value=0;fills();assert.equal(rows.length,0);assert.equal(messages['page-info'],'No matching fills');
$('fill-session-only').checked=false;fills();assert.equal(rows.length,1);
// Finder intersects explicit records and preserves cursor/winner until inspection.
simulation.intents=[
 {index:0,asset:'all',kind:'normal',outcome:'filled',reasons:[],requested_quantity:1,filled_quantity:1,expired_quantity:0},
 {index:1,asset:'all',kind:'normal',outcome:'partial',reasons:['volume_capacity'],requested_quantity:-2,filled_quantity:-1,expired_quantity:-1},
 {index:1,asset:'OTHER',kind:'risk',outcome:'blocked',reasons:['volume_capacity'],requested_quantity:-3,filled_quantity:0,expired_quantity:-3}];
assert.equal(matchingIntents().length,3);
$('finder-outcome').value='incomplete';assert.equal(matchingIntents().length,2);
$('finder-asset').value='all';assert.equal(matchingIntents().length,1);
$('finder-reason').value='cash_limit';assert.equal(matchingIntents().length,0);
intentPage=99;intentFinder();assert.equal(intentPage,0);assert.match(messages['finder-count'],/No matching attempts/);
assert.equal($('finder-previous').disabled,true);assert.equal($('finder-next').disabled,true);
findAttempts(false);assert.equal(matchingIntents().length,3);assert.equal(location.hash,'finder');
$('finder-asset').value='all';findAttempts(true);assert.equal(matchingIntents().length,1);
assert.equal(tables['finder-table'][0][2],'-2');assert.equal(tables['finder-table'][0][4],'-1');
const cursorBefore=Number($('session').value);inspectIntent(999);assert.equal(Number($('session').value),cursorBefore);
inspectIntent(0);assert.equal(Number($('session').value),0);assert.equal(location.hash,'execution');assert.equal(D.winner,'candidate');
findAttempts(false);simulation.intents=Array.from({length:25},(_,i)=>({...simulation.intents[0],asset:'A'+i}));
intentFinder();assert.equal(tables['finder-table'].length,12);assert.equal($('finder-next').disabled,false);
intentPage=2;intentFinder();assert.equal(tables['finder-table'].length,1);assert.equal($('finder-next').disabled,true);
intentPage=99;intentFinder();assert.equal(intentPage,2);
delete simulation.intents;intentFinder();assert.equal(intentPage,0);assert.match(messages['finder-count'],/No matching attempts/);
// Shared asset context synchronizes exact names and preserves portfolio evidence.
simulation.intents=[{index:0,asset:'all',kind:'normal',outcome:'partial',reasons:['volume_capacity'],requested_quantity:2,filled_quantity:1,expired_quantity:1}];
simulation.fills=[makeFill('all',1),makeFill('OTHER',-2)];
$('session').value=0;$('fill-side').value='all';$('fill-session-only').checked=false;
$('finder-outcome').value='incomplete';$('finder-reason').value='volume_capacity';
const immutableBefore=JSON.stringify(D.results),winnerBefore=D.winner;
page=4;intentPage=4;runCommand('asset #1');
assert.equal(assetFocus,'all');assert.equal(page,0);assert.equal(intentPage,0);
for(const id of ['asset-focus','fill-asset','finder-asset'])assert.equal($(id).value,'all');
assert.equal(tables.holdings.length,1);assert.deepEqual(tables.holdings[0],['all','11']);
assert.equal(rows.length,1);assert.equal(tables['intent-table'].length,1);assert.equal(matchingIntents().length,1);
assert.equal($('finder-outcome').value,'incomplete');assert.equal($('finder-reason').value,'volume_capacity');
const allPortfolioMetrics=JSON.stringify($('execution-metrics').children);
runCommand('asset #3');assert.equal(assetFocus,'Asset / with spaces');
assert.deepEqual(tables.holdings[0],['Asset / with spaces','33'],'Filtering must preserve original asset-position column');
assert.equal(rows.length,0);assert.equal($('intent-table').children.length,0);
assert.ok(messages['execution-note'].includes('No matching request rows for Asset / with spaces'));
assert.equal(JSON.stringify($('execution-metrics').children),allPortfolioMetrics,'Asset detail focus does not filter portfolio execution totals');
for(const command of ['asset #0','asset #4','asset #-1','asset #1.5','asset #9007199254740993','asset all']){
 runCommand(command);assert.equal(assetFocus,'Asset / with spaces');
 for(const id of ['asset-focus','fill-asset','finder-asset'])assert.equal($(id).value,assetFocus);
}
setAssetFocus('unknown');assert.equal(assetFocus,'Asset / with spaces');
runCommand('strategy other');assert.equal(assetFocus,'Asset / with spaces');runCommand('strategy candidate');
runCommand('asset');assert.equal(assetFocus,'');assert.equal(tables.holdings.length,3);assert.equal(rows.length,2);
for(const id of ['asset-focus','fill-asset','finder-asset'])assert.equal($(id).value,'');
$('fill-side').value='sell';$('fill-session-only').checked=true;setAssetFocus('OTHER');
assert.equal(rows.length,1);assert.equal(rows[0][1],'OTHER');assert.equal(rows[0][2],'-2');
assert.equal($('fill-side').value,'sell');assert.equal($('fill-session-only').checked,true);
assert.equal(matchingIntents().length,0,'Asset/reason/outcome intersection remains explicit');
findAttempts(false);assert.equal(assetFocus,'');assert.equal($('finder-reason').value,'');assert.equal($('finder-outcome').value,'');
assert.equal($('fill-side').value,'sell');assert.equal($('fill-session-only').checked,true);
assert.equal(JSON.stringify(D.results),immutableBefore);assert.equal(D.winner,winnerBefore);

// History never executes recall, preserves unfinished input, and remains bounded.
assert.equal(recallCommand('ArrowUp','draft'),null);
executeCommand('  help  ');assert.deepEqual(commandHistory,['help']);executeCommand('help');assert.equal(commandHistory.length,1);
assert.equal(recallCommand('ArrowUp','draft'), 'help');assert.equal(recallCommand('ArrowUp','ignored'),'help');
assert.equal(recallCommand('ArrowDown','ignored'),'draft');assert.equal(recallCommand('ArrowDown','draft'),'draft');
assert.equal(recallCommand('ArrowLeft','draft'),null);
const priorLength=commandHistory.length;executeCommand('   ');assert.equal(commandHistory.length,priorLength);
for(let i=0;i<105;i++)executeCommand('unsupported '+i);
assert.equal(commandHistory.length,100);assert.equal(commandHistory[0],'unsupported 5');
assert.equal(historyIndex,100);assert.equal(D.winner,'candidate');
runCommand('process.exit()'); assert.match(messages['command-result'], /Unknown command/);
runCommand('help'); assert.equal($('help-dialog').open, true);
assert.equal($('command-search').focused,true);
assert.equal($('command-choices').children.length,commandOptions.length);
renderCommandChoices('  STRATEGY OTHER ');assert.equal($('command-choices').children.length,1);
const beforePaletteInspections=inspections,beforePaletteUpdates=updates,beforePaletteCurrent=current;
$('command-choices').children[0].listeners.click();
assert.equal($('command').value,'strategy other');assert.equal($('command').focused,true);
assert.equal($('help-dialog').open,false);assert.equal(inspections,beforePaletteInspections);
assert.equal(updates,beforePaletteUpdates);assert.equal(current,beforePaletteCurrent);assert.equal(D.winner,'candidate');
renderCommandChoices('no-such-command');assert.equal($('command-choices').children.length,0);assert.match(messages['command-matches'],/No matching command/);
$('section-jump').value='finder';jumpSection();assert.equal($('section-jump').value,'');
const jumpScrollCount=scrolls.length;$('section-jump').value='finder';jumpSection();assert.equal(scrolls.length,jumpScrollCount+1);
jumpSection();assert.equal(scrolls.length,jumpScrollCount+1);
const beforeLinkScrolls=scrolls.length;let prevented=0;
const linkEvent={preventDefault(){prevented++},currentTarget:{getAttribute(name){assert.equal(name,'href');return '#finder'}}};
navigateLink(linkEvent);navigateLink(linkEvent);assert.equal(prevented,2);assert.equal(scrolls.length,beforeLinkScrolls+2);
assert.deepEqual(scrolls.slice(-2),['finder','finder']);assert.deepEqual(focusCalls.slice(-2),['finder','finder']);

`;
vm.runInNewContext(scenario, {assert}, {timeout: 2000, filename: 'chronal-report-logic'});
console.log('PASS static anchors, commands, frozen selection, dates, interval accounting, cursor mapping, filters, refit boundaries, model context, execution/event inspection, precision, intent finder, command history, searchable palette, shared exact asset focus, source cutoff timestamps and focused repeated section navigation.');
console.log('Logic checks only; browser interaction and visual checks remain separate.');
