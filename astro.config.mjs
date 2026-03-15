// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	redirects: {
		"/": "/guides/sigero",
	},
	integrations: [
		starlight({

			title: 'Integraciones Purolomo',
			defaultLocale: 'es',
			lastUpdated: true,
			 credits: false,
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/withastro/starlight' }],
			sidebar: [
				{
					label: 'Integraciones',
					items: [
						
						{ label: 'Integration Sigero', slug: 'guides/sigero' },
					],
				},
			],
		}),
	],
	site: 'https://Virtual-Office-Group.github.io',
	base: 'IntegracionesPurolomo',
});
