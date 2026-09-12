"use client"

import { useEffect, useRef, type ComponentPropsWithoutRef } from "react"
import { useInView, useMotionValue, useReducedMotion, useSpring } from "motion/react"

import { cn } from "@/lib/utils"

interface NumberTickerProps extends ComponentPropsWithoutRef<"span"> {
  value: number
  startValue?: number
  direction?: "up" | "down"
  delay?: number
  decimalPlaces?: number
}

export function NumberTicker({
  value,
  startValue = 0,
  direction = "up",
  delay = 0,
  className,
  decimalPlaces = 0,
  ...props
}: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const motionValue = useMotionValue(direction === "down" ? startValue : value) // the server renders the final value
  const springValue = useSpring(motionValue, {
    damping: 60,
    stiffness: 100,
  })
  const isInView = useInView(ref, { once: true, margin: "0px" })
  const reduce = useReducedMotion()
  const fmt = (n: number) =>
    Intl.NumberFormat("en-US", { minimumFractionDigits: decimalPlaces, maximumFractionDigits: decimalPlaces }).format(Number(n.toFixed(decimalPlaces)))

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null
    let settle: ReturnType<typeof setTimeout> | null = null

    if (isInView) {
      if (reduce) {
        motionValue.jump(direction === "down" ? startValue : value)
        return
      }
      motionValue.jump(direction === "down" ? value : startValue)
      springValue.jump(direction === "down" ? value : startValue)
      timer = setTimeout(() => {
        motionValue.set(direction === "down" ? startValue : value)
        settle = setTimeout(() => {  // whatever the spring did, the figure on screen ends exact
          if (ref.current) ref.current.textContent = fmt(direction === "down" ? startValue : value)
        }, 3000)
      }, delay * 1000)
    }

    return () => {
      if (timer !== null) clearTimeout(timer)
      if (settle !== null) clearTimeout(settle)
    }
  }, [motionValue, springValue, isInView, delay, value, direction, startValue, reduce])

  useEffect(
    () =>
      springValue.on("change", (latest) => {
        if (ref.current) {
          // a spring approaches its target without reaching it: inside one display step, show the real number
          const target = direction === "down" ? startValue : value
          // a spring approaches its target without reaching it, so the last stretch shows the real number
          const near = Math.max(Math.pow(10, -decimalPlaces) / 2, Math.abs(target) * 0.01)
          const shown = Math.abs(target - latest) < near ? target : latest
          ref.current.textContent = Intl.NumberFormat("en-US", {
            minimumFractionDigits: decimalPlaces,
            maximumFractionDigits: decimalPlaces,
          }).format(Number(shown.toFixed(decimalPlaces)))
        }
      }),
    [springValue, decimalPlaces, direction, startValue, value]
  )

  return (
    <span
      ref={ref}
      className={cn(
        "inline-block tabular-nums",
        className
      )}
      {...props}
    >
      {fmt(direction === "down" ? startValue : value)}
    </span>
  )
}
