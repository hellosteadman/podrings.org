import { success as toast } from './toast'

(
    () => {
        const selector = '[data-pr-action="copy"][data-pr-text]'

        document.addEventListener('click',
            async (e) => {
                const btn = e.target.matches(selector) ? e.target : e.target.closest(selector)
                const text = btn ? btn.getAttribute('data-pr-text') : ''

                if (!btn) {
                    return
                }

                e.preventDefault()

                try {
                    await navigator.clipboard.writeText(text)
                } catch (err) {
                    console.error('Error copying text', err)
                    return
                }

                toast('Copied to clipboard.', 'clipboard-check-fill')
                return
            }
        )
    }
)()
