import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Shorten long skill names so they fit on the chart axis
const shorten = (text) => (text.length > 20 ? `${text.slice(0, 19)}…` : text);

export default function ProgressChart({ variant = 'comparison', data = [], centerValue = '', centerLabel = '' }) {
  // ---------- Donut chart ----------
  if (variant === 'donut') {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    // If there is nothing to show, draw an empty grey ring
    const chartData = total === 0 ? [{ name: 'No activities', value: 1, color: '#e2e8f0' }] : data;

    return (
      <div className="donut-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius="62%"
              outerRadius="90%"
              paddingAngle={total === 0 ? 0 : 2}
              stroke="none"
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            {total > 0 && <Tooltip />}
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center">
          <strong>{centerValue}</strong>
          <span>{centerLabel}</span>
        </div>
      </div>
    );
  }

  // ---------- Comparison bar chart (Current vs Target) ----------
  const height = Math.max(280, data.length * 40 + 70);

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
          <XAxis type="number" domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} tick={{ fontSize: 12, fill: '#64748b' }} />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fontSize: 12, fill: '#334155' }}
            tickFormatter={shorten}
          />
          <Tooltip cursor={{ fill: '#eff6ff' }} />
          <Legend />
          <Bar dataKey="Current" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={10} />
          <Bar dataKey="Target" fill="#0f2a5c" radius={[0, 4, 4, 0]} barSize={10} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}