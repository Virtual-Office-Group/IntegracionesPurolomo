// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightImageZoom from 'starlight-image-zoom'

// https://astro.build/config
export default defineConfig({
	vite: {
    	assetsInclude: ['**/*.py'], // <--- Agrega esta línea
  	},
	integrations: [
		starlight({
			plugins: [starlightImageZoom()],
			title: 'Integraciones Purolomo',
			favicon: './public/logo.jpg',
			defaultLocale: 'es',
			lastUpdated: true,
			locales: {
				root: {
				label: 'Español',
				lang: 'es', // Esto es vital
				},
			},
			credits: false,
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/withastro/starlight' }],
			logo: {
				src: './public/logo.jpg', 
				alt: 'Integraciones Purolomo',
				replacesTitle: false,
			},
			sidebar: [
				{
					label: 'Integraciones',
					items: [
						
						{ label: 'Sistema Sigero', slug: 'guides/sigero' },
						{ label: 'Nomina - Business Central',slug:'guides/paysheet'}
					],
				},
			],
		}),
	],
	site: 'https://Virtual-Office-Group.github.io',
	base: 'IntegracionesPurolomo',
	redirects:{
		'/':'guides/sigero'
	}
});
