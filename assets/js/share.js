(() => {
    const getPopupSize = (url) => {
        const domain = new URL(url).hostname

        if (domain.includes('twitter.com')) {
            return {
                width: 550,
                height: 300
            }
        }

        if (domain.includes('facebook.com')) {
            return {
                width: 600,
                height: 500
            }
        }

        if (domain.includes('linkedin.com')) {
            return {
                width: 600,
                height: 600
            }
        }

        if (domain.includes('reddit.com')) {
            return {
                width: 800,
                height: 600
            }
        }

        return {
            width: 600,
            height: 500
        }
    }

    document.addEventListener('click',
        async (e) => {
            const btn = e.target.matches('[data-pr-action="share"]') ? e.target : e.target.closest('[data-pr-action="share"]')
            const href = btn ? btn.href : ''

            if (!btn || !href) {
                return
            }

            e.preventDefault()

            const { width, height } = getPopupSize(href)
            const left = (screen.width - width) / 2
            const top = (screen.height - height) / 2

            window.open(href, 'share-popup', `width=${width},height=${height},top=${top},left=${left},scrollbars=yes,resizable=yes`)
        }
    )
})()
