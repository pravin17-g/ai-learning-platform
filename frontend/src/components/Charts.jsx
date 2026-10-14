import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const COLORS = {
  current: "#2563eb", target: "#9ca3af", gap: "#dc2626",
  Completed: "#16a34a", "In progress": "#f59e0b", "Not started": "#9ca3af",
};

// Current vs target proficiency per skill
export function ProficiencyChart({ skills }) {
  const data = skills.map((s) => ({ skill: s.name, Current: s.current_level, Target: s.target_level }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(260, data.length * 56)}>
      <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 5]} allowDecimals={false} />
        <YAxis type="category" dataKey="skill" width={170} />
        <Tooltip />
        <Legend />
        <Bar dataKey="Current" fill={COLORS.current} />
        <Bar dataKey="Target" fill={COLORS.target} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Remaining gap (in levels) per skill
export function GapChart({ skills }) {
  const data = skills.map((s) => ({ skill: s.name, Gap: s.gap }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(240, data.length * 44)}>
      <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 5]} allowDecimals={false} />
        <YAxis type="category" dataKey="skill" width={170} />
        <Tooltip />
        <Bar dataKey="Gap" fill={COLORS.gap} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Learning progress: activities by status
export function ProgressChart({ progress }) {
  if (!progress || progress.total === 0) {
    return (
      <div style={{ textAlign: "center", padding: "24px 16px", color: "var(--muted)", fontSize: "0.92rem" }}>
        No learning activities to chart yet.
      </div>
    );
  }

  const isAllNotStarted = progress.completed === 0 && progress.in_progress === 0;

  const data = isAllNotStarted
    ? [{ name: "Not started", value: progress.total, color: "#cbd5e1" }]
    : [
        { name: "Completed", value: progress.completed, color: COLORS.Completed },
        { name: "In progress", value: progress.in_progress, color: COLORS["In progress"] },
        { name: "Not started", value: progress.not_started, color: COLORS["Not started"] },
      ].filter((d) => d.value > 0);

  return (
    <div style={{ width: "100%", maxWidth: "380px", margin: "0 auto" }}>
      <div className="donut-wrap" style={{ height: "180px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={56}
              outerRadius={76}
              paddingAngle={isAllNotStarted ? 0 : 2}
              stroke="none"
            >
              {data.map((d) => (
                <Cell key={d.name} fill={d.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(val, name) => [
                `${val} activities (${progress.total > 0 ? Math.round((val / progress.total) * 100) : 0}%)`,
                name,
              ]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center">
          <strong>{progress.percent}%</strong>
          <span>{isAllNotStarted ? "Not Started" : "Completed"}</span>
        </div>
      </div>

      <div className="legend" style={{ marginTop: "4px" }}>
        <span>
          <span className="legend-dot" style={{ background: COLORS.Completed }} />
          Completed ({progress.completed})
        </span>
        <span>
          <span className="legend-dot" style={{ background: COLORS["In progress"] }} />
          In progress ({progress.in_progress})
        </span>
        <span>
          <span className="legend-dot" style={{ background: COLORS["Not started"] }} />
          Not started ({progress.not_started})
        </span>
      </div>

      {isAllNotStarted && (
        <p style={{ textAlign: "center", fontSize: "0.82rem", color: "var(--muted)", marginTop: "8px" }}>
          All {progress.total} activities are awaiting start. Update any activity to track your progress.
        </p>
      )}
    </div>
  );
}