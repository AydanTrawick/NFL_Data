'use client';
import {motion,useReducedMotion} from 'motion/react';
export default function Template({children}:{children:React.ReactNode}){const reduce=useReducedMotion();return <motion.div initial={reduce?false:{opacity:.65,y:8}} animate={{opacity:1,y:0}} transition={{duration:.25}}>{children}</motion.div>}
