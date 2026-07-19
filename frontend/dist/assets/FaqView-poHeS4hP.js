import{$ as e,A as t,Ct as n,E as r,F as i,I as a,M as o,N as s,P as c,S as l,U as u,W as d,bt as f,c as p,d as m,g as h,h as g,i as _,it as v,l as y,m as b,s as x,t as S,u as C}from"./_plugin-vue_export-helper-BnoIuITy.js";import{C as w,R as T,X as E,Z as D,r as O,t as k}from"./basecomponent-Dbv6nt4q.js";import{n as A,t as ee}from"./ripple-D4n4TQgR.js";import{D as te,T as ne,r as j}from"./index-Bf2Mz9Zv.js";import{t as M}from"./chevrondown-vcnLFsYV.js";import{t as N}from"./PageHeader-By2CVi-e.js";import{t as P}from"./EmptyState-D8UFD5zi.js";import{t as F}from"./chevronright-BGRlyQi5.js";var I={name:`ChevronUpIcon`,extends:A};function L(e){return V(e)||B(e)||z(e)||R()}function R(){throw TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function z(e,t){if(e){if(typeof e==`string`)return H(e,t);var n={}.toString.call(e).slice(8,-1);return n===`Object`&&e.constructor&&(n=e.constructor.name),n===`Map`||n===`Set`?Array.from(e):n===`Arguments`||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?H(e,t):void 0}}function B(e){if(typeof Symbol<`u`&&e[Symbol.iterator]!=null||e[`@@iterator`]!=null)return Array.from(e)}function V(e){if(Array.isArray(e))return H(e)}function H(e,t){(t==null||t>e.length)&&(t=e.length);for(var n=0,r=Array(t);n<t;n++)r[n]=e[n];return r}function U(e,n,r,i,a,o){return t(),m(`svg`,l({width:`14`,height:`14`,viewBox:`0 0 14 14`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`},e.pti()),L(n[0]||=[p(`path`,{d:`M12.2097 10.4113C12.1057 10.4118 12.0027 10.3915 11.9067 10.3516C11.8107 10.3118 11.7237 10.2532 11.6506 10.1792L6.93602 5.46461L2.22139 10.1476C2.07272 10.244 1.89599 10.2877 1.71953 10.2717C1.54307 10.2556 1.3771 10.1808 1.24822 10.0593C1.11933 9.93766 1.035 9.77633 1.00874 9.6011C0.982477 9.42587 1.0158 9.2469 1.10338 9.09287L6.37701 3.81923C6.52533 3.6711 6.72639 3.58789 6.93602 3.58789C7.14565 3.58789 7.3467 3.6711 7.49502 3.81923L12.7687 9.09287C12.9168 9.24119 13 9.44225 13 9.65187C13 9.8615 12.9168 10.0626 12.7687 10.2109C12.616 10.3487 12.4151 10.4207 12.2097 10.4113Z`,fill:`currentColor`},null,-1)]),16)}I.render=U;var W=O.extend({name:`accordioncontent`,classes:{root:`p-accordioncontent`,contentWrapper:`p-accordioncontent-wrapper`,content:`p-accordioncontent-content`}}),G={name:`AccordionContent`,extends:{name:`BaseAccordionContent`,extends:k,props:{as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:W,provide:function(){return{$pcAccordionContent:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],computed:{id:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},ariaLabelledby:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},attrs:function(){return l(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{id:this.id,role:`region`,"aria-labelledby":this.ariaLabelledby,"data-pc-name":`accordioncontent`,"data-p-active":this.$pcAccordionPanel.active}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}}}};function K(e,n,r,i,o,c){return e.asChild?s(e.$slots,`default`,{key:1,class:f(e.cx(`root`)),active:c.$pcAccordionPanel.active,a11yAttrs:c.a11yAttrs}):(t(),y(ne,l({key:0,name:`p-collapsible`},e.ptm(`transition`,c.ptParams)),{default:u(function(){return[!c.$pcAccordion.lazy||c.$pcAccordionPanel.active?d((t(),y(a(e.as),l({key:0,class:e.cx(`root`)},c.attrs),{default:u(function(){return[p(`div`,l({class:e.cx(`contentWrapper`)},e.ptm(`contentWrapper`,c.ptParams)),[p(`div`,l({class:e.cx(`content`)},e.ptm(`content`,c.ptParams)),[s(e.$slots,`default`)],16)],16)]}),_:3},16,[`class`])),[[te,c.$pcAccordion.lazy?!0:c.$pcAccordionPanel.active]]):C(``,!0)]}),_:3},16))}G.render=K;var q=O.extend({name:`accordionheader`,classes:{root:`p-accordionheader`,toggleicon:`p-accordionheader-toggle-icon`}}),J={name:`AccordionHeader`,extends:{name:`BaseAccordionHeader`,extends:k,props:{as:{type:[String,Object],default:`BUTTON`},asChild:{type:Boolean,default:!1}},style:q,provide:function(){return{$pcAccordionHeader:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`,`$pcAccordionPanel`],methods:{onFocus:function(){this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onClick:function(){!this.$pcAccordion.selectOnFocus&&this.changeActiveValue()},onKeydown:function(e){switch(e.code){case`ArrowDown`:this.onArrowDownKey(e);break;case`ArrowUp`:this.onArrowUpKey(e);break;case`Home`:this.onHomeKey(e);break;case`End`:this.onEndKey(e);break;case`Enter`:case`NumpadEnter`:case`Space`:this.onEnterKey(e);break}},onArrowDownKey:function(e){var t=this.findNextPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onHomeKey(e),e.preventDefault()},onArrowUpKey:function(e){var t=this.findPrevPanel(this.findPanel(e.currentTarget));t?this.changeFocusedPanel(e,t):this.onEndKey(e),e.preventDefault()},onHomeKey:function(e){var t=this.findFirstPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEndKey:function(e){var t=this.findLastPanel();this.changeFocusedPanel(e,t),e.preventDefault()},onEnterKey:function(e){this.changeActiveValue(),e.preventDefault()},findPanel:function(e){return e?.closest(`[data-pc-name="accordionpanel"]`)},findHeader:function(e){return E(e,`[data-pc-name="accordionheader"]`)},findNextPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.nextElementSibling;return t?w(t,`data-p-disabled`)?this.findNextPanel(t):this.findHeader(t):null},findPrevPanel:function(e){var t=arguments.length>1&&arguments[1]!==void 0&&arguments[1]?e:e.previousElementSibling;return t?w(t,`data-p-disabled`)?this.findPrevPanel(t):this.findHeader(t):null},findFirstPanel:function(){return this.findNextPanel(this.$pcAccordion.$el.firstElementChild,!0)},findLastPanel:function(){return this.findPrevPanel(this.$pcAccordion.$el.lastElementChild,!0)},changeActiveValue:function(){this.$pcAccordion.updateValue(this.$pcAccordionPanel.value)},changeFocusedPanel:function(e,t){T(this.findHeader(t))}},computed:{id:function(){return`${this.$pcAccordion.$id}_accordionheader_${this.$pcAccordionPanel.value}`},ariaControls:function(){return`${this.$pcAccordion.$id}_accordioncontent_${this.$pcAccordionPanel.value}`},attrs:function(){return l(this.asAttrs,this.a11yAttrs,this.ptmi(`root`,this.ptParams))},asAttrs:function(){return this.as===`BUTTON`?{type:`button`,disabled:this.$pcAccordionPanel.disabled}:void 0},a11yAttrs:function(){return{id:this.id,tabindex:this.$pcAccordion.tabindex,"aria-expanded":this.$pcAccordionPanel.active,"aria-controls":this.ariaControls,"data-pc-name":`accordionheader`,"data-p-disabled":this.$pcAccordionPanel.disabled,"data-p-active":this.$pcAccordionPanel.active,onFocus:this.onFocus,onKeydown:this.onKeydown}},ptParams:function(){return{context:{active:this.$pcAccordionPanel.active}}},dataP:function(){return D({active:this.$pcAccordionPanel.active})}},components:{ChevronUpIcon:I,ChevronDownIcon:M},directives:{ripple:ee}};function Y(e,n,r,o,c,p){var m=i(`ripple`);return e.asChild?s(e.$slots,`default`,{key:1,class:f(e.cx(`root`)),active:p.$pcAccordionPanel.active,a11yAttrs:p.a11yAttrs,onClick:p.onClick}):d((t(),y(a(e.as),l({key:0,"data-p":p.dataP,class:e.cx(`root`),onClick:p.onClick},p.attrs),{default:u(function(){return[s(e.$slots,`default`,{active:p.$pcAccordionPanel.active}),s(e.$slots,`toggleicon`,{active:p.$pcAccordionPanel.active,class:f(e.cx(`toggleicon`))},function(){return[p.$pcAccordionPanel.active?(t(),y(a(p.$pcAccordion.$slots.collapseicon?p.$pcAccordion.$slots.collapseicon:p.$pcAccordion.collapseIcon?`span`:`ChevronUpIcon`),l({key:0,class:[p.$pcAccordion.collapseIcon,e.cx(`toggleicon`)],"aria-hidden":`true`},e.ptm(`toggleicon`,p.ptParams)),null,16,[`class`])):(t(),y(a(p.$pcAccordion.$slots.expandicon?p.$pcAccordion.$slots.expandicon:p.$pcAccordion.expandIcon?`span`:`ChevronDownIcon`),l({key:1,class:[p.$pcAccordion.expandIcon,e.cx(`toggleicon`)],"aria-hidden":`true`},e.ptm(`toggleicon`,p.ptParams)),null,16,[`class`]))]})]}),_:3},16,[`data-p`,`class`,`onClick`])),[[m]])}J.render=Y;var X=O.extend({name:`accordionpanel`,classes:{root:function(e){var t=e.instance,n=e.props;return[`p-accordionpanel`,{"p-accordionpanel-active":t.active,"p-disabled":n.disabled}]}}}),Z={name:`AccordionPanel`,extends:{name:`BaseAccordionPanel`,extends:k,props:{value:{type:[String,Number],default:void 0},disabled:{type:Boolean,default:!1},as:{type:[String,Object],default:`DIV`},asChild:{type:Boolean,default:!1}},style:X,provide:function(){return{$pcAccordionPanel:this,$parentInstance:this}}},inheritAttrs:!1,inject:[`$pcAccordion`],computed:{active:function(){return this.$pcAccordion.isItemActive(this.value)},attrs:function(){return l(this.a11yAttrs,this.ptmi(`root`,this.ptParams))},a11yAttrs:function(){return{"data-pc-name":`accordionpanel`,"data-p-disabled":this.disabled,"data-p-active":this.active}},ptParams:function(){return{context:{active:this.active}}}}};function re(e,n,r,i,o,c){return e.asChild?s(e.$slots,`default`,{key:1,class:f(e.cx(`root`)),active:c.active,a11yAttrs:c.a11yAttrs}):(t(),y(a(e.as),l({key:0,class:e.cx(`root`)},c.attrs),{default:u(function(){return[s(e.$slots,`default`)]}),_:3},16,[`class`]))}Z.render=re;var Q=O.extend({name:`accordion`,style:`
    .p-accordionpanel {
        display: flex;
        flex-direction: column;
        border-style: solid;
        border-width: dt('accordion.panel.border.width');
        border-color: dt('accordion.panel.border.color');
    }

    .p-accordionheader {
        all: unset;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: dt('accordion.header.padding');
        color: dt('accordion.header.color');
        background: dt('accordion.header.background');
        border-style: solid;
        border-width: dt('accordion.header.border.width');
        border-color: dt('accordion.header.border.color');
        font-weight: dt('accordion.header.font.weight');
        border-radius: dt('accordion.header.border.radius');
        transition:
            background dt('accordion.transition.duration'),
            color dt('accordion.transition.duration'),
            outline-color dt('accordion.transition.duration'),
            box-shadow dt('accordion.transition.duration');
        outline-color: transparent;
    }

    .p-accordionpanel:first-child > .p-accordionheader {
        border-width: dt('accordion.header.first.border.width');
        border-start-start-radius: dt('accordion.header.first.top.border.radius');
        border-start-end-radius: dt('accordion.header.first.top.border.radius');
    }

    .p-accordionpanel:last-child > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.bottom.border.radius');
    }

    .p-accordionpanel:last-child.p-accordionpanel-active > .p-accordionheader {
        border-end-start-radius: dt('accordion.header.last.active.bottom.border.radius');
        border-end-end-radius: dt('accordion.header.last.active.bottom.border.radius');
    }

    .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.color');
    }

    .p-accordionpanel:not(.p-disabled) .p-accordionheader:focus-visible {
        box-shadow: dt('accordion.header.focus.ring.shadow');
        outline: dt('accordion.header.focus.ring.width') dt('accordion.header.focus.ring.style') dt('accordion.header.focus.ring.color');
        outline-offset: dt('accordion.header.focus.ring.offset');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) > .p-accordionheader:hover {
        background: dt('accordion.header.hover.background');
        color: dt('accordion.header.hover.color');
    }

    .p-accordionpanel:not(.p-accordionpanel-active):not(.p-disabled) .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader {
        background: dt('accordion.header.active.background');
        color: dt('accordion.header.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover {
        background: dt('accordion.header.active.hover.background');
        color: dt('accordion.header.active.hover.color');
    }

    .p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader:hover .p-accordionheader-toggle-icon {
        color: dt('accordion.header.toggle.icon.active.hover.color');
    }

    .p-accordioncontent {
        display: grid;
        grid-template-rows: 1fr;
    }

    .p-accordioncontent-wrapper {
        min-height: 0;
    }

    .p-accordioncontent-content {
        border-style: solid;
        border-width: dt('accordion.content.border.width');
        border-color: dt('accordion.content.border.color');
        background-color: dt('accordion.content.background');
        color: dt('accordion.content.color');
        padding: dt('accordion.content.padding');
    }
`,classes:{root:`p-accordion p-component`}}),$={name:`Accordion`,extends:{name:`BaseAccordion`,extends:k,props:{value:{type:[String,Number,Array],default:void 0},multiple:{type:Boolean,default:!1},lazy:{type:Boolean,default:!1},tabindex:{type:Number,default:0},selectOnFocus:{type:Boolean,default:!1},expandIcon:{type:String,default:void 0},collapseIcon:{type:String,default:void 0},activeIndex:{type:[Number,Array],default:null}},style:Q,provide:function(){return{$pcAccordion:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`update:value`,`update:activeIndex`,`tab-open`,`tab-close`,`tab-click`],data:function(){return{d_value:this.value}},watch:{value:function(e){this.d_value=e},activeIndex:{immediate:!0,handler:function(e){this.hasAccordionTab&&(this.d_value=this.multiple?e?.map(String):e?.toString())}}},methods:{isItemActive:function(e){return this.multiple?this.d_value?.includes(e):this.d_value===e},updateValue:function(e){var t=this.isItemActive(e);this.multiple?t?this.d_value=this.d_value.filter(function(t){return t!==e}):this.d_value?this.d_value.push(e):this.d_value=[e]:this.d_value=t?null:e,this.$emit(`update:value`,this.d_value),this.$emit(`update:activeIndex`,this.multiple?this.d_value?.map(Number):Number(this.d_value)),this.$emit(t?`tab-close`:`tab-open`,{originalEvent:void 0,index:Number(e)})},isAccordionTab:function(e){return e.type.name===`AccordionTab`},getTabProp:function(e,t){return e.props?e.props[t]:void 0},getKey:function(e,t){return this.getTabProp(e,`header`)||t},getHeaderPT:function(e,t){var n=this;return{root:l({onClick:function(e){return n.onTabClick(e,t)}},this.getTabProp(e,`headerProps`),this.getTabPT(e,`header`,t)),toggleicon:l(this.getTabProp(e,`headeractionprops`),this.getTabPT(e,`headeraction`,t))}},getContentPT:function(e,t){return{root:l(this.getTabProp(e,`contentProps`),this.getTabPT(e,`toggleablecontent`,t)),transition:this.getTabPT(e,`transition`,t),content:this.getTabPT(e,`content`,t)}},getTabPT:function(e,t,n){var r=this.tabs.length,i={props:e.props||{},parent:{instance:this,props:this.$props,state:this.$data},context:{index:n,count:r,first:n===0,last:n===r-1,active:this.isItemActive(`${n}`)}};return l(this.ptm(`accordiontab.${t}`,i),this.ptmo(this.getTabProp(e,`pt`),t,i))},onTabClick:function(e,t){this.$emit(`tab-click`,{originalEvent:e,index:t})}},computed:{tabs:function(){var e=this;return this.$slots.default().reduce(function(t,n){return e.isAccordionTab(n)?t.push(n):n.children&&n.children instanceof Array&&n.children.forEach(function(n){e.isAccordionTab(n)&&t.push(n)}),t},[])},hasAccordionTab:function(){return this.tabs.length}},components:{AccordionPanel:Z,AccordionHeader:J,AccordionContent:G,ChevronUpIcon:I,ChevronRightIcon:F}};function ie(e,r,i,d,p,h){var v=c(`AccordionHeader`),b=c(`AccordionContent`),x=c(`AccordionPanel`);return t(),m(`div`,l({class:e.cx(`root`)},e.ptmi(`root`)),[h.hasAccordionTab?(t(!0),m(_,{key:0},o(h.tabs,function(r,i){return t(),y(x,{key:h.getKey(r,i),value:`${i}`,pt:{root:h.getTabPT(r,`root`,i)},disabled:h.getTabProp(r,`disabled`)},{default:u(function(){return[g(v,{class:f(h.getTabProp(r,`headerClass`)),pt:h.getHeaderPT(r,i)},{toggleicon:u(function(n){return[n.active?(t(),y(a(e.$slots.collapseicon?e.$slots.collapseicon:e.collapseIcon?`span`:`ChevronDownIcon`),l({key:0,class:[e.collapseIcon,n.class],"aria-hidden":`true`},{ref_for:!0},h.getTabPT(r,`headericon`,i)),null,16,[`class`])):(t(),y(a(e.$slots.expandicon?e.$slots.expandicon:e.expandIcon?`span`:`ChevronUpIcon`),l({key:1,class:[e.expandIcon,n.class],"aria-hidden":`true`},{ref_for:!0},h.getTabPT(r,`headericon`,i)),null,16,[`class`]))]}),default:u(function(){return[r.children&&r.children.headericon?(t(),y(a(r.children.headericon),{key:0,isTabActive:h.isItemActive(`${i}`),active:h.isItemActive(`${i}`),index:i},null,8,[`isTabActive`,`active`,`index`])):C(``,!0),r.props&&r.props.header?(t(),m(`span`,l({key:1,ref_for:!0},h.getTabPT(r,`headertitle`,i)),n(r.props.header),17)):C(``,!0),r.children&&r.children.header?(t(),y(a(r.children.header),{key:2})):C(``,!0)]}),_:2},1032,[`class`,`pt`]),g(b,{pt:h.getContentPT(r,i)},{default:u(function(){return[(t(),y(a(r)))]}),_:2},1032,[`pt`])]}),_:2},1032,[`value`,`pt`,`disabled`])}),128)):s(e.$slots,`default`,{key:1})],16)}$.render=ie;var ae={class:`cat`},oe={class:`glass card`},se={class:`answer`},ce=S(h({__name:`FaqView`,setup(i){let a=e([]),s=e(!0),c=x(()=>{let e=new Map;for(let t of a.value){let n=t.category||`General`;e.has(n)||e.set(n,[]),e.get(n).push(t)}return[...e.entries()]});return r(async()=>{try{let{data:e}=await j.faq();a.value=Array.isArray(e)?e:[]}finally{s.value=!1}}),(e,r)=>(t(),m(`div`,null,[g(N,{title:`FAQ`,subtitle:`Answers to common questions`}),!s.value&&!a.value.length?(t(),y(P,{key:0,title:`No FAQs yet`,text:`Check back soon or open a support ticket.`})):C(``,!0),(t(!0),m(_,null,o(c.value,([e,r])=>(t(),m(`div`,{key:e,class:`block`},[p(`h3`,ae,n(e),1),p(`div`,oe,[g(v($),null,{default:u(()=>[(t(!0),m(_,null,o(r,e=>(t(),y(v(Z),{key:e.id,value:e.id},{default:u(()=>[g(v(J),null,{default:u(()=>[b(n(e.question),1)]),_:2},1024),g(v(G),null,{default:u(()=>[p(`div`,se,n(e.answer),1)]),_:2},1024)]),_:2},1032,[`value`]))),128))]),_:2},1024)])]))),128))]))}}),[[`__scopeId`,`data-v-89c6060c`]]);export{ce as default};