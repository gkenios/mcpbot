import { useEffect, RefObject, DependencyList } from 'react';

const useAutoScroll = (
  ref: RefObject<HTMLElement | null>,
  dependency: DependencyList,
  scrollBehavior: ScrollBehavior = "smooth"
) => {
  useEffect(() => {
    if (ref.current) {
      // Double animation frame for guaranteed layout completion
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          ref.current?.scrollTo({
            top: ref.current.scrollHeight,
            behavior: scrollBehavior,
          });
        });
      });
    }
  }, dependency);  // eslint-disable-line react-hooks/exhaustive-deps
};

export default useAutoScroll;
