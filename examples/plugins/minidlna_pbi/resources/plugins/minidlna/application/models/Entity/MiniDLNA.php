<?php

namespace Entity;

use Doctrine\Common\Collections\ArrayCollection;

/**
 * @Entity
 * @Table(name="minidlna")
 */
class MiniDLNA
{
    /**
     * @var     int
     * @Id
     * @Column(type="integer")
     * @GeneratedValue
     */
    protected $id = null;

    /**
     * @var     boolean
     * @Column(type="boolean")
     */
    protected $enabled = false;

    /**
     * @var     boolean
     * @Column(type="boolean")
     */
    protected $debug = false;

    /**
     * @var     string
     * @Column(type="string")
     */
    protected $media_dir = null;


    public function __construct()
    {
        //$this->setGroups(new ArrayCollection());
    }

    /**
     * @return  int
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @param   int     $id
     * @return  void
     */
    public function setId($id)
    {
        $this->id = $id;
    }

    /**
     * @return  string
     */
    public function getEnabled()
    {
        return $this->enabled;
    }

    /**
     * @param   string  $username
     * @return  void
     */
    public function setEnabled($enabled)
    {
        $this->enabled = $enabled;
    }

    /**
     * @return  string
     */
    public function getMediaDir()
    {
        return $this->media_dir;
    }

    /**
     * @param   string  $username
     * @return  void
     */
    public function setMediaDir($mediadir)
    {
        $this->media_dir = $mediadir;
    }

}
