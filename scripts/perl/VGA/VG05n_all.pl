#! /usr/bin/perl -w
# VG05_exc.pl -- MySQL:ECM_Acts_VG:ivv7srv16.uni-muenster.de
# legt auf der Basis von VG05_all Einzeltabellen fŸr jedes Kapitel und fŸr die Summierung an
# Vorlage von Klaus Wachtel, geŠndert von Volker KrŸger

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_VG:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

###Chapter Number eintragen, 0 fŸr Summierung###
my $chn = $ARGV[0];

my $chnstr;

if ($chn < 10)
{
	if ($chn == 0)
	{
		$chnstr = '0';
	} else {
		$chnstr = '0'.$chn;
	}
} else {
	$chnstr = $chn;
}

my $source = '`ECM_Acts_VG`.`VG05_all`';
my $wert = '`ECM_Acts_Mss`.`ActsMsListVal`';
my $target = '`ECM_Acts_VG`.`VG05'.$chnstr.'_all`';

my $sumtxtn;
my $qmtn;
my $gtxtn;
my $uegesn;
my $uegesqn;

if ($chn > 0)
{
	$sumtxtn = 'SUMTXT'.$chn;
	$qmtn = 'QMT'.$chn;
	$gtxtn = 'GTXT'.$chn;
	$uegesn = 'UEGES'.$chn;
	$uegesqn = 'UEGESQ'.$chn;
} else {
	$sumtxtn = 'SUMTXT';
	$qmtn = 'QMT';
	$gtxtn = 'GTXT';
	$uegesn = 'UEGES';
	$uegesqn = 'UEGESQ';
}

$dbh->do ("DROP TABLE IF EXISTS $target;");

$dbh->do ("CREATE  TABLE  $target 
	(`MS` int( 6  )  NOT  NULL ,
	 `VGMS` int( 6  )  NOT  NULL ,
	 `CHECK` varchar( 1  )  NOT  NULL ,
	 `GTXT` int( 5  )  NOT  NULL ,
	 `UEGES` int( 5  )  NOT  NULL ,
	 `UEGESQ` decimal( 4, 1  )  NOT  NULL ,
	 KEY  `MS` (  `MS`  ) ,
	 KEY  `VGMS` (  `VGMS`  )  ) ENGINE  =  MyISAM  DEFAULT CHARSET  = latin1;");

my ($sth, @ary, $ary, $hsnr, @msl, $ms, $limit, $qmt);

$dbh->do ("UPDATE $wert SET `CHECK` = '' WHERE 1"); # my $wert = '`ECM_Acts_Mss`.`ActsMsListVal`';

$sth = $dbh->prepare ("SELECT HSNR FROM $wert WHERE `CHECK` NOT LIKE 'e'"); # $wert = ActsMsListVal
$sth->execute();
	
while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
}

foreach $ms(@msl)
{
	undef $sth;
	###beschrŠnkt die Auswahl auf die Vergleichshss., die mit $ms an mindestens der HŠlfte der in $ms belegten variierten Stellen gemeinsam Text haben 
	($limit) = $dbh->selectrow_array ("SELECT $sumtxtn FROM $wert WHERE HSNR = $ms");
	
	$sth = $dbh->prepare ("SELECT `MS`, `CHECK`, `VGMS`, $gtxtn, $uegesn, $uegesqn FROM $source WHERE (`MS` = $ms OR `VGMS`= $ms) AND $gtxtn > $limit/2 ORDER BY $uegesqn DESC");
	
	$sth->execute();
	
	if (defined $sth)
	{
		while (@ary = $sth->fetchrow_array())
		{
			if ($ms == $ary[0])
			{
				$dbh->do ("INSERT INTO $target (MS, `CHECK`, VGMS, GTXT, UEGES, UEGESQ) 
				VALUES ($ary[0], '$ary[1]', $ary[2], $ary[3], $ary[4], $ary[5])");
			} else {
				$dbh->do ("INSERT INTO $target (MS, `CHECK`, VGMS, GTXT, UEGES, UEGESQ) 
				VALUES ($ary[2], '$ary[1]', $ary[0], $ary[3], $ary[4], $ary[5])");				
			}
		}
	}
			
	$dbh->do ("UPDATE $wert SET `CHECK` = 'e' WHERE HSNR = $ms");
}

$sth->finish ();

$dbh->disconnect ();

exit (0);
