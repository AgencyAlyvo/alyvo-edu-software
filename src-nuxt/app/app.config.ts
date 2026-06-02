export default defineAppConfig({
  ui: {
    toast: {
      slots: {
        root: 'bg-[#071022] ring-0 border border-[#2f3d67] shadow-[0_20px_60px_rgba(0,0,0,0.6)] rounded-lg',
        title: 'text-sm font-semibold text-white',
        description: 'text-xs text-[#9ba3bd] leading-relaxed',
        close: 'text-[#9ba3bd] hover:text-white',
        icon: 'shrink-0 size-5',
        progress: 'absolute inset-x-0 bottom-0 opacity-40',
      },
      variants: {
        color: {
          primary: {
            root: 'border-l-[3px] border-l-[#9a65d5]',
            icon: 'text-[#9a65d5]',
          },
          success: {
            root: 'border-l-[3px] border-l-emerald-500',
            icon: 'text-emerald-400',
          },
          error: {
            root: 'border-l-[3px] border-l-red-500',
            icon: 'text-red-400',
          },
          warning: {
            root: 'border-l-[3px] border-l-amber-500',
            icon: 'text-amber-400',
          },
          info: {
            root: 'border-l-[3px] border-l-sky-500',
            icon: 'text-sky-400',
          },
          neutral: {
            root: 'border-l-[3px] border-l-[#485780]',
            icon: 'text-[#9ba3bd]',
          },
        },
      },
    },
  },
})
