import { useState } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

const PasswordInput = ({ value, onChange }: Props) => {
  const [show, setShow] = useState(false);

  return (
    <div className="password-input">
      <input
        type={show ? "text" : "password"}
        placeholder="Password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
      />
      <button type="button" onClick={() => setShow((prev) => !prev)}>
        {show ? "Hide" : "Show"}
      </button>
    </div>
  );
};

export default PasswordInput;