interface CustomSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  className?: string;
  color?: "primary" | "secondary" | "accent";
}

export const CustomSlider = ({ 
  value, 
  onChange, 
  min = 0, 
  max = 100, 
  className = "",
  color = "primary"
}: CustomSliderProps) => {
  const colorClasses = {
    primary: "bg-primary",
    secondary: "bg-secondary", 
    accent: "bg-accent"
  };

  return (
    <div className={`relative ${className}`}>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
        style={{
          background: 'transparent'
        }}
      />
      <div 
        className={`absolute top-0 left-0 h-2 ${colorClasses[color]} rounded-lg transition-all duration-200 pointer-events-none`}
        style={{ width: `${(value / max) * 100}%` }}
      />
    </div>
  );
};
