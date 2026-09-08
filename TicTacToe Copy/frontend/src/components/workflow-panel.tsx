import { ArrowRight, Bot, CheckCircle2, FileText, GitPullRequest, LockKeyhole, ShieldCheck, Terminal, TestTube2 } from "lucide-react";
import { agents, decisions, deliveryContext, taskCards } from "~/demo-data";

export function WorkflowPanel() {
  return (
    <section aria-labelledby="workflow-heading" className="mx-auto mb-10 w-full max-w-7xl rounded-[2rem] border border-white/10 bg-[#11141c] p-5 text-[#f7f7f2] shadow-2xl shadow-black/20 sm:p-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#d8ff56]"><span className="h-px w-7 bg-[#d8ff56]" /> The delivery trace</p>
          <h2 id="workflow-heading" className="mt-3 text-3xl font-semibold tracking-[-0.05em]">Agent workflow</h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/50">A presentation layer for the decisions, ownership boundaries, and evidence behind the playable app. It shows why we did something—not private chain-of-thought.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-white/45"><span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">Epic</span><ArrowRight size={13} /><span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">Sprint</span><ArrowRight size={13} /><span className="rounded-full border border-[#d8ff56]/30 bg-[#d8ff56]/10 px-3 py-1.5 text-[#d8ff56]">Task</span></div>
      </div>

      <div aria-label="Delivery context" className="mt-6 grid gap-3 md:grid-cols-3">
        <a className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 no-underline transition hover:border-[#d8ff56]/30" href={deliveryContext.epic.url} rel="noreferrer" target="_blank">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#d8ff56]">Epic · outcome</span>
          <strong className="mt-2 block text-sm text-white">{deliveryContext.epic.title}</strong>
          <span className="mt-1 block text-xs leading-5 text-white/60">{deliveryContext.epic.detail}</span>
        </a>
        <a className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 no-underline transition hover:border-[#d8ff56]/30" href={deliveryContext.sprint.url} rel="noreferrer" target="_blank">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#d8ff62]">Sprint · timebox</span>
          <strong className="mt-2 block text-sm text-white">{deliveryContext.sprint.title}</strong>
          <span className="mt-1 block text-xs leading-5 text-white/60">{deliveryContext.sprint.detail}</span>
        </a>
        <a className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 no-underline transition hover:border-[#d8ff56]/30" href={deliveryContext.source} rel="noreferrer" target="_blank">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#d8ff62]">Task DB · source</span>
          <strong className="mt-2 block text-sm text-white">Bounded execution cards</strong>
          <span className="mt-1 block text-xs leading-5 text-white/60">Acceptance criteria, owner, status, branch, PR, and test evidence.</span>
        </a>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_.95fr]">
        <div>
          <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-white">Decision log</h3><span className="text-[10px] uppercase tracking-[0.14em] text-white/30">intent → consequence</span></div>
          <div className="grid gap-3">{decisions.map((decision) => <article className="rounded-2xl border border-white/10 bg-white/[0.025] p-4" key={decision.title}><p className="text-sm font-semibold text-white">{decision.title}</p><p className="mt-2 text-xs leading-5 text-white/60">{decision.detail}</p><div className="mt-3 flex gap-2 text-[11px] leading-5 text-[#d8ff56]"><ArrowRight size={13} className="mt-1 shrink-0" />{decision.consequence}</div></article>)}</div>
        </div>

        <div>
          <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-white">Bounded ownership</h3><span className="flex items-center gap-1 text-[10px] uppercase tracking-[0.14em] text-[#d8ff56]"><LockKeyhole size={12} /> one writer</span></div>
          <div className="grid gap-2">{agents.map((agent) => <article className="flex gap-3 rounded-2xl border border-white/10 bg-white/[0.025] p-3" key={agent.name}><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#d8ff56]/10 text-[#d8ff56]"><Bot size={15} /></span><div className="min-w-0"><div className="flex flex-wrap items-baseline gap-x-2 gap-y-1"><h4 className="text-xs font-semibold text-white">{agent.name}</h4><span className="text-[10px] text-white/55">{agent.domain}</span></div><p className="mt-1 text-[11px] text-white/60">{agent.owns}</p><div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-white/55"><span className="inline-flex items-center gap-1"><Terminal size={11} />{agent.writeZone}</span><span className="inline-flex items-center gap-1"><ShieldCheck size={11} />{agent.approval}</span></div></div></article>)}</div>
        </div>
      </div>

      <div className="mt-8 border-t border-white/10 pt-6"><div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-white">Task evidence</h3><span className="text-[10px] uppercase tracking-[0.14em] text-white/55">acceptance is the contract</span></div><div className="grid gap-2 md:grid-cols-2">{taskCards.map((task) => <article className="rounded-2xl border border-white/10 bg-white/[0.025] p-4" key={task.id}><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] font-semibold tracking-[0.14em] text-white/55">{task.id}</span><h4 className="mt-1 text-sm font-semibold text-white">{task.title}</h4></div><span className="inline-flex items-center gap-1 whitespace-nowrap text-[10px] text-[#d8ff56]"><CheckCircle2 size={13} /> {task.status}</span></div><p className="mt-2 text-xs leading-5 text-white/60">{task.acceptance}</p><div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-white/55"><span className="inline-flex items-center gap-1"><Bot size={11} />{task.owner}</span><span className="inline-flex items-center gap-1"><TestTube2 size={11} />{task.evidence}</span></div><div className="mt-3 flex flex-wrap gap-2 text-[10px]"><a className="inline-flex items-center gap-1 rounded-full border border-white/10 px-2 py-1 text-white/65 hover:border-[#d8ff56]/40 hover:text-[#d8ff56]" href={task.sourceUrl} rel="noreferrer" target="_blank"><FileText size={11} /> Notion task</a><a aria-label={task.prLabel} className="inline-flex items-center gap-1 rounded-full border border-white/10 px-2 py-1 text-white/65 hover:border-[#d8ff56]/40 hover:text-[#d8ff56]" href={task.prUrl} rel="noreferrer" target="_blank"><GitPullRequest size={11} /> {task.prLabel}</a></div></article>)}</div></div>

      <div className="mt-6 flex flex-col gap-3 border-t border-white/10 pt-5 text-[11px] text-white/60 sm:flex-row sm:items-center sm:justify-between"><span className="inline-flex items-center gap-2"><FileText size={13} className="text-[#d8ff56]" /> Notion → task contract → agent handoff → PR → QA</span><span className="inline-flex items-center gap-2"><GitPullRequest size={13} className="text-[#d8ff56]" /> Human acceptance stays authoritative</span></div>
    </section>
  );
}
