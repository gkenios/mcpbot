import { FC } from "react";

const Spinner: FC = () => {
  return (
    <>
      <style>
        {`
          @keyframes waveBounce {
            0%, 20% {
              transform: translateY(0);
              opacity: 0.4;
            }
            40% {
              transform: translateY(-8px);
              opacity: 1;
            }
            60%, 100% {
              transform: translateY(0);
              opacity: 0.4;
            }
          }
        `}
      </style>
      <div style={{
        display: "flex",
        alignItems: "flex-end",
        gap: "0.3rem",
        height: "1.5rem",
        paddingBottom: "0.3rem",
      }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: "0.5rem",
              height: "0.5rem",
              backgroundColor: "#aaa",
              borderRadius: "50%",
              animation: "waveBounce 1.8s infinite ease-in-out",
              animationDelay: `${i * 0.2}s`
            }}
          />
        ))}
      </div>
    </>
  );
};

export default Spinner;
