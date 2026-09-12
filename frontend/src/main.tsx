import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Bot, Plus, Send, Settings2 } from 'lucide-react';
import './style.css';

type Step = { tool_name?: string; status?: string };
type Message = { role: string; content: string; steps?: Step[] };

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/v1/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: '我的工作台' }) })
      .then((response) => response.json()).then((body) => setSessionId(body.data.id)).catch(() => setError('无法连接后端服务'));
  }, []);

  const send = async () => {
    if (!input.trim() || !sessionId || busy) return;
    const question = input;
    setInput(''); setError(''); setMessages((items) => [...items, { role: 'user', content: question }]); setBusy(true);
    try {
      const response = await fetch(`/api/v1/sessions/${sessionId}/messages`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: question, model: 'mock' }) });
      const body = await response.json();
      if (!body.success) throw new Error(body.error?.message || '请求失败');
      setMessages((items) => [...items, { role: 'assistant', content: body.data.answer, steps: body.data.steps }]);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : '请求失败'); } finally { setBusy(false); }
  };

  return <div className="app"><aside><div className="brand"><Bot size={22} /> AI Workbench</div><button className="new" onClick={() => setMessages([])}><Plus size={17} /> 新建会话</button><div className="section">会话</div><div className="session active">我的工作台</div><div className="bottom"><Settings2 size={17} /> 设置</div></aside><main><header><div><h1>我的工作台</h1><span>Agent 工具调用实验室</span></div><select><option>Mock Model · local</option></select></header><div className="chat">{messages.length === 0 ? <div className="empty"><Bot size={42} /><h2>开始一次对话</h2><p>输入任务，Agent 将在这里展示工具选择与执行结果。</p></div> : messages.map((message, index) => <div className={'msg ' + message.role} key={index}><b>{message.role === 'user' ? '你' : 'Agent'}</b><div>{message.content}</div>{message.steps?.filter((step) => step.tool_name).map((step, stepIndex) => <div className="step" key={stepIndex}>工具：{step.tool_name} · {step.status}</div>)}</div>)}</div>{error && <div className="error">{error}</div>}<div className="composer"><textarea value={input} disabled={busy} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="描述一个任务，例如：查询现在的时间" /><button onClick={send} disabled={busy} title="发送"><Send size={18} /></button></div></main></div>;
}

createRoot(document.getElementById('root')!).render(<App />);
