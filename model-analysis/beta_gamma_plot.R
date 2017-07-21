require(ggplot2)
pref <- 'src_RJ-tgt_RJ-grav_model_rss_aic_beta_1.50-1.80_gamma_2.50-3.10'
df2 <- read.csv(paste0('../data/',pref,'.csv'))

p = ggplot(df2, aes(x=beta, y=gamma, z=Log_10.ER.)) + theme_bw()
c.plot <- p + stat_contour(breaks=seq(1,10), aes(colour = ..level..)) +
  ggtitle(bquote(F[jk]%prop%T[j]~m[k]^beta/~r[jk]^gamma)) + 
  xlab(expression(beta)) + 
  ylab(expression(gamma)) +
  labs(colour=expression(Log[10](ER)))
ggsave(paste0(pref,'.eps'))

c.plot2 <- p + 
  geom_raster(aes(fill=Log_10.ER.)) + 
  labs(fill=expression(Log[10](ER))) + 
  stat_contour(breaks=c(0.5,1,2,5,10), color='black') +
  scale_fill_gradientn(colours=RColorBrewer::brewer.pal(9, 'Blues'), 
                       na.value='transparent', breaks=seq(0,10,2), 
                       labels=seq(0,10,2), limits=c(0,10)) + 
  ggtitle(bquote(F[jk]%prop%T[j]~m[k]^beta/~r[jk]^gamma)) + 
  xlab(expression(beta)) + 
  ylab(expression(gamma))
  
ggsave(paste0(pref,'_filled.eps'))